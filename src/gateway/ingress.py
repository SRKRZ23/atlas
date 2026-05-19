"""
ATLAS Gateway — Voice ingress + SOUF AI DPI.

Pipeline:
  1. Speechmatics RT transcription (voice → text, < 200ms)
  2. SOUF AI DPI inspection (text → ALLOW/DENY/HUMAN_REVIEW, < 1ms)
  3. Forward to orchestrator (if ALLOW)
  4. Return 403 + regulation citation (if DENY)
  5. Escalate to Gemini human-review (if HUMAN_REVIEW)
"""
from __future__ import annotations

import os
import time
import logging
import asyncio
import json
import sys
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

# SOUF AI DPI engine (reused)
DPI_PATH = Path(__file__).resolve().parents[4] / "transforming_enterprise" / "souf-ai" / "demo"
sys.path.insert(0, str(DPI_PATH))

logger = logging.getLogger(__name__)


@dataclass
class IngressResult:
    text: str
    action: str           # ALLOW / DENY / HUMAN_REVIEW
    rule: str
    message: str
    citation: str
    dpi_latency_ms: float
    voice_latency_ms: float
    request_id: str


def _gen_request_id() -> str:
    import uuid
    return f"atlas_{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"


# ── SOUF AI DPI ───────────────────────────────────────────────────────────────

try:
    import dpi_engine as dpi
    _DPI_AVAILABLE = True
    logger.info("SOUF AI DPI engine loaded")
except ImportError:
    _DPI_AVAILABLE = False
    logger.warning("SOUF AI DPI engine not available — running without inspection")


def inspect_prompt(text: str, mode: str = "base") -> tuple[str, str, str, float]:
    """
    Inspect prompt with SOUF AI DPI.
    Returns (action, rule, message, latency_ms).
    """
    if not _DPI_AVAILABLE:
        return "ALLOW", "dpi_unavailable", "", 0.0

    t0 = time.perf_counter()
    meta = dpi.inspect(text)
    decision = dpi.evaluate(meta, mode=mode)
    latency_ms = (time.perf_counter() - t0) * 1000

    return decision.action, decision.rule, decision.message, latency_ms


# ── Speechmatics RT transcription ────────────────────────────────────────────

def transcribe_audio_file(audio_path: str) -> tuple[str, float]:
    """
    Transcribe an audio file using Speechmatics batch API.
    Returns (transcript, latency_ms).
    Falls back to empty string if API key not set.
    """
    api_key = os.environ.get("SPEECHMATICS_API_KEY", "")
    if not api_key:
        logger.warning("SPEECHMATICS_API_KEY not set — skipping transcription")
        return "", 0.0

    try:
        import httpx
        t0 = time.perf_counter()

        # Speechmatics batch transcription API
        url = "https://asr.api.speechmatics.com/v2/jobs/"
        headers = {"Authorization": f"Bearer {api_key}"}

        with open(audio_path, "rb") as f:
            files = {"data_file": f}
            config = {
                "type": "transcription",
                "transcription_config": {
                    "language": "en",
                    "operating_point": "enhanced",
                    "enable_entities": True,
                }
            }
            resp = httpx.post(
                url, headers=headers,
                files=files,
                data={"config": json.dumps(config)},
                timeout=30.0
            )

        if resp.status_code == 201:
            job_id = resp.json()["id"]
            # Poll for result
            for _ in range(30):
                time.sleep(2)
                result_resp = httpx.get(
                    f"{url}{job_id}/transcript",
                    headers={**headers, "Accept": "application/json"},
                    timeout=10.0
                )
                if result_resp.status_code == 200:
                    data = result_resp.json()
                    words = [w["content"] for w in data.get("results", [])
                             if w.get("type") == "word"]
                    transcript = " ".join(words)
                    latency_ms = (time.perf_counter() - t0) * 1000
                    return transcript, latency_ms

    except Exception as e:
        logger.error("Speechmatics transcription error: %s", e)

    return "", 0.0


def process_text_input(
    text: str,
    dpi_mode: str = "base",
    request_id: Optional[str] = None,
) -> IngressResult:
    """
    Main entry point for text inputs (typed or pre-transcribed).
    Applies SOUF AI DPI and returns IngressResult.
    """
    if not request_id:
        request_id = _gen_request_id()

    action, rule, message, dpi_latency = inspect_prompt(text, mode=dpi_mode)

    return IngressResult(
        text=text,
        action=action,
        rule=rule,
        message=message,
        citation="",
        dpi_latency_ms=dpi_latency,
        voice_latency_ms=0.0,
        request_id=request_id,
    )


def process_audio_input(
    audio_path: str,
    dpi_mode: str = "base",
    request_id: Optional[str] = None,
) -> IngressResult:
    """
    Full pipeline: audio → Speechmatics → SOUF AI DPI → IngressResult.
    """
    if not request_id:
        request_id = _gen_request_id()

    transcript, voice_latency = transcribe_audio_file(audio_path)
    if not transcript:
        return IngressResult(
            text="", action="ERROR", rule="transcription_failed",
            message="Audio transcription failed or Speechmatics API key not set.",
            citation="", dpi_latency_ms=0.0,
            voice_latency_ms=voice_latency, request_id=request_id,
        )

    action, rule, message, dpi_latency = inspect_prompt(transcript, mode=dpi_mode)

    return IngressResult(
        text=transcript,
        action=action, rule=rule, message=message, citation="",
        dpi_latency_ms=dpi_latency,
        voice_latency_ms=voice_latency,
        request_id=request_id,
    )
