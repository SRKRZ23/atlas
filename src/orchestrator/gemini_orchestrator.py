"""
ATLAS Orchestrator — Gemini Pro multi-step task planning.

Receives ALLOW'd prompt from gateway → decomposes into subtasks →
dispatches each subtask to Featherless router → collects results →
synthesises final response.
"""
from __future__ import annotations

import os
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

_GEMINI_AVAILABLE = False
try:
    import google.generativeai as genai  # type: ignore
    _GEMINI_AVAILABLE = True
except ImportError:
    logger.warning("google-generativeai not installed — orchestrator in mock mode")


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class Subtask:
    id: str
    description: str
    task_type: str          # code / medical / multilingual / general / financial / infra
    tool: Optional[str]     # search / database / kraken / vultr / none
    depends_on: list[str] = field(default_factory=list)


@dataclass
class ExecutionPlan:
    request_id: str
    original_prompt: str
    subtasks: list[Subtask]
    planning_latency_ms: float
    model_used: str


@dataclass
class OrchestratorResult:
    request_id: str
    plan: ExecutionPlan
    subtask_results: list[dict]
    final_response: str
    total_latency_ms: float
    human_review_requested: bool = False


# ── System prompt for Gemini ──────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are ATLAS, an enterprise multi-agent orchestrator. Your job is to decompose a user request into a precise, ordered list of subtasks.

For each subtask output a JSON object with fields:
- id: string like "t1", "t2", ...
- description: what this subtask does
- task_type: one of [code, medical, multilingual, general, financial, infra]
- tool: one of [search, database, kraken, vultr, none]
- depends_on: list of subtask ids this depends on (empty list if independent)

Output ONLY a JSON array of subtask objects, no other text.

Rules:
- Maximum 6 subtasks
- Always end with a "general" type synthesis subtask with tool "none" that depends on all others
- Choose task_type based on domain: financial queries → financial, infrastructure → infra, code → code
- Use tool "kraken" for market data / trading actions
- Use tool "vultr" for infrastructure provisioning
- Use tool "search" for web/KB lookups
- Use tool "database" for internal data queries"""


_SYNTHESIS_PROMPT = """You are ATLAS, an enterprise AI assistant. Given the user's original request and the results from your subtasks, synthesise a clear, professional response.

Original request: {prompt}

Subtask results:
{results}

Write a concise, accurate response addressing the original request."""


# ── Orchestrator ──────────────────────────────────────────────────────────────

class GeminiOrchestrator:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY", "")
        self._model = None
        if _GEMINI_AVAILABLE and self.api_key:
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel("gemini-2.0-flash-exp")
            logger.info("Gemini orchestrator initialised (gemini-2.0-flash-exp)")
        else:
            logger.warning("Gemini orchestrator in mock mode (no API key or library)")

    def plan(self, prompt: str, request_id: str) -> ExecutionPlan:
        t0 = time.perf_counter()
        model_used = "gemini-2.0-flash-exp"

        if self._model:
            subtasks = self._plan_with_gemini(prompt)
        else:
            subtasks = self._mock_plan(prompt)
            model_used = "mock"

        latency_ms = (time.perf_counter() - t0) * 1000
        return ExecutionPlan(
            request_id=request_id,
            original_prompt=prompt,
            subtasks=subtasks,
            planning_latency_ms=latency_ms,
            model_used=model_used,
        )

    def _plan_with_gemini(self, prompt: str) -> list[Subtask]:
        try:
            full_prompt = f"{_SYSTEM_PROMPT}\n\nUser request: {prompt}"
            response = self._model.generate_content(full_prompt)
            text = response.text.strip()
            # Strip markdown fences if present
            if text.startswith("```"):
                text = "\n".join(text.split("\n")[1:])
            if text.endswith("```"):
                text = "\n".join(text.split("\n")[:-1])
            raw = json.loads(text)
            return [
                Subtask(
                    id=s["id"],
                    description=s["description"],
                    task_type=s.get("task_type", "general"),
                    tool=s.get("tool", "none"),
                    depends_on=s.get("depends_on", []),
                )
                for s in raw
            ]
        except Exception as e:
            logger.error("Gemini planning error: %s — using mock plan", e)
            return self._mock_plan("")

    def _mock_plan(self, prompt: str) -> list[Subtask]:
        text_lower = prompt.lower()
        if any(w in text_lower for w in ["bitcoin", "btc", "eth", "crypto", "price", "trade", "market"]):
            return [
                Subtask("t1", "Fetch current market data", "financial", "kraken"),
                Subtask("t2", "Search for relevant news", "general", "search", ["t1"]),
                Subtask("t3", "Synthesise market summary", "general", "none", ["t1", "t2"]),
            ]
        if any(w in text_lower for w in ["server", "vm", "instance", "deploy", "infrastructure"]):
            return [
                Subtask("t1", "Query current infrastructure state", "infra", "vultr"),
                Subtask("t2", "Search best practices", "general", "search"),
                Subtask("t3", "Generate infrastructure plan", "infra", "none", ["t1", "t2"]),
            ]
        if any(w in text_lower for w in ["code", "debug", "function", "class", "implement"]):
            return [
                Subtask("t1", "Search documentation", "code", "search"),
                Subtask("t2", "Generate code solution", "code", "none", ["t1"]),
                Subtask("t3", "Synthesise final response", "general", "none", ["t2"]),
            ]
        return [
            Subtask("t1", "Search for relevant information", "general", "search"),
            Subtask("t2", "Query internal database", "general", "database", ["t1"]),
            Subtask("t3", "Synthesise final response", "general", "none", ["t1", "t2"]),
        ]

    def synthesise(self, plan: ExecutionPlan, subtask_results: list[dict]) -> str:
        if not self._model:
            return self._mock_synthesis(plan, subtask_results)

        results_text = "\n".join(
            f"[{r['subtask_id']}] {r['description']}: {r.get('output', '(no output)')}"
            for r in subtask_results
        )
        synthesis_prompt = _SYNTHESIS_PROMPT.format(
            prompt=plan.original_prompt,
            results=results_text,
        )
        try:
            response = self._model.generate_content(synthesis_prompt)
            return response.text.strip()
        except Exception as e:
            logger.error("Gemini synthesis error: %s", e)
            return self._mock_synthesis(plan, subtask_results)

    def _mock_synthesis(self, plan: ExecutionPlan, subtask_results: list[dict]) -> str:
        steps = [f"- {r['description']}: {r.get('output', '(completed)')}" for r in subtask_results]
        return (
            f"Task completed successfully.\n\n"
            f"Executed {len(subtask_results)} subtasks:\n" +
            "\n".join(steps) +
            f"\n\nOriginal request: {plan.original_prompt}"
        )

    def escalate_to_human_review(self, prompt: str, request_id: str, reason: str) -> str:
        logger.warning("Human review escalation: %s — reason: %s", request_id, reason)
        if self._model:
            try:
                review_prompt = (
                    f"You are a compliance reviewer. The following prompt was flagged for human review. "
                    f"Reason: {reason}\n\nPrompt: {prompt}\n\n"
                    "Provide a brief risk assessment and recommended action (ALLOW/BLOCK/MODIFY)."
                )
                response = self._model.generate_content(review_prompt)
                return response.text.strip()
            except Exception as e:
                logger.error("Gemini human review error: %s", e)
        return (
            f"HUMAN REVIEW REQUIRED\n"
            f"Request ID: {request_id}\n"
            f"Reason: {reason}\n"
            f"Action: Escalated to compliance team for manual review."
        )
