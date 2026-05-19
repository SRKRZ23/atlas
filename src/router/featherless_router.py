"""
ATLAS Router — Featherless model selection per subtask type.

Model IDs confirmed from AI Agent Olympics 2026 kick-off (Isaac, Featherless):
  - agentic    → MiniMax-M2.5     (Excellent in agentic tool use — Isaac, Featherless)
  - code       → DeepSeek-V3.2
  - multilingual / long-context → Kimi-K2.5
  - financial / infra / general  → Llama-3.3-70B
"""
from __future__ import annotations

import os
import logging
import time
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# ── Model routing table ───────────────────────────────────────────────────────

_TASK_TYPE_TO_MODEL = {
    "agentic":       "MiniMaxAI/MiniMax-M2.5",
    "code":          "deepseek-ai/DeepSeek-V3.2",
    "multilingual":  "moonshotai/Kimi-K2.5",
    "financial":     "meta-llama/Llama-3.3-70B-Instruct",
    "infra":         "meta-llama/Llama-3.3-70B-Instruct",
    "general":       "meta-llama/Llama-3.3-70B-Instruct",
}

_MODEL_DISPLAY_NAMES = {
    "MiniMaxAI/MiniMax-M2.5":               "MiniMax-M2.5",
    "deepseek-ai/DeepSeek-V3.2":            "DeepSeek-V3.2",
    "moonshotai/Kimi-K2.5":                 "Kimi-K2.5",
    "meta-llama/Llama-3.3-70B-Instruct":    "Llama-3.3-70B",
}

_FEATHERLESS_BASE_URL = "https://api.featherless.ai/v1"


@dataclass
class RouterResult:
    subtask_id: str
    description: str
    task_type: str
    model_id: str
    model_display: str
    output: str
    latency_ms: float
    tokens_used: int


# ── Router ────────────────────────────────────────────────────────────────────

class FeatherlessRouter:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("FEATHERLESS_API_KEY", "")
        self._client = None
        if self.api_key:
            try:
                from openai import OpenAI  # type: ignore
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=_FEATHERLESS_BASE_URL,
                )
                logger.info("Featherless router initialised")
            except ImportError:
                logger.warning("openai package not installed — router in mock mode")
        else:
            logger.warning("FEATHERLESS_API_KEY not set — router in mock mode")

    def route(
        self,
        subtask_id: str,
        description: str,
        task_type: str,
        context: str = "",
    ) -> RouterResult:
        model_id = _TASK_TYPE_TO_MODEL.get(task_type, _TASK_TYPE_TO_MODEL["general"])
        model_display = _MODEL_DISPLAY_NAMES.get(model_id, model_id)

        t0 = time.perf_counter()

        if self._client:
            output, tokens = self._call_featherless(model_id, description, context)
        else:
            output, tokens = self._mock_response(task_type, description)

        latency_ms = (time.perf_counter() - t0) * 1000

        logger.info(
            "Router: %s → %s (%.1fms, %d tokens)",
            subtask_id, model_display, latency_ms, tokens,
        )

        return RouterResult(
            subtask_id=subtask_id,
            description=description,
            task_type=task_type,
            model_id=model_id,
            model_display=model_display,
            output=output,
            latency_ms=latency_ms,
            tokens_used=tokens,
        )

    def _call_featherless(self, model_id: str, description: str, context: str) -> tuple[str, int]:
        messages = [
            {"role": "system", "content": "You are a precise enterprise AI assistant. Answer concisely and accurately."},
        ]
        if context:
            messages.append({"role": "user", "content": f"Context: {context}\n\nTask: {description}"})
        else:
            messages.append({"role": "user", "content": description})

        try:
            resp = self._client.chat.completions.create(
                model=model_id,
                messages=messages,
                max_tokens=512,
                temperature=0.1,
            )
            output = resp.choices[0].message.content or ""
            tokens = resp.usage.total_tokens if resp.usage else 0
            return output, tokens
        except Exception as e:
            logger.error("Featherless call error (model=%s): %s", model_id, e)
            return f"[Model error: {e}]", 0

    def _mock_response(self, task_type: str, description: str) -> tuple[str, int]:
        responses = {
            "agentic":       f"Agentic execution: {description} — Tool calls planned and sequenced. Execution chain: search → filter → act → verify.",
            "code":          f"Code solution for: {description}\n```python\n# Implementation\ndef solution():\n    return 'result'\n```",
            "multilingual":  f"Multilingual processing: {description} — Analysis complete across supported language variants with long-context coherence.",
            "financial":     f"Financial analysis: {description} — Current market conditions indicate moderate volatility. Risk assessment: MEDIUM.",
            "infra":         f"Infrastructure analysis: {description} — Recommended configuration: 2vCPU, 4GB RAM, SSD storage on Vultr.",
            "general":       f"Analysis complete: {description} — Relevant information gathered and processed.",
        }
        output = responses.get(task_type, responses["general"])
        return output, len(output.split()) * 2
