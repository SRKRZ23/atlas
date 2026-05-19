"""
ATLAS Agent — full pipeline orchestration.

Pipeline:
  1. gateway/ingress.py  — voice → text + SOUF AI DPI
  2. orchestrator/       — Gemini Pro task planning
  3. router/             — Featherless model per subtask
  4. tools/              — search / database / kraken / vultr
  5. audit/              — Ed25519 signed trail per action
  6. synthesis           — Gemini Pro final response
"""
from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from gateway.ingress import process_text_input, process_audio_input, IngressResult
from orchestrator.gemini_orchestrator import GeminiOrchestrator, ExecutionPlan, Subtask
from router.featherless_router import FeatherlessRouter, RouterResult
from tools.tool_executor import execute_tool, ToolResult
from audit.audit_chain import AgentAuditTrail

logger = logging.getLogger(__name__)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


@dataclass
class AgentResponse:
    request_id: str
    input_text: str
    dpi_action: str
    plan: Optional[ExecutionPlan]
    subtask_results: list[dict]
    final_response: str
    audit_trail: dict
    total_latency_ms: float
    human_review_requested: bool = False
    error: str = ""


class AtlasAgent:
    def __init__(self):
        self.orchestrator = GeminiOrchestrator()
        self.router = FeatherlessRouter()
        self._audit = AgentAuditTrail()

    def run_text(self, text: str, dpi_mode: str = "base") -> AgentResponse:
        t_start = time.perf_counter()

        # Step 1: DPI inspection
        ingress = process_text_input(text, dpi_mode=dpi_mode)
        self._audit.log_ingress(
            ingress.request_id, ingress.text,
            ingress.action, ingress.rule,
        )

        if ingress.action == "DENY":
            return self._denied(ingress, t_start)

        if ingress.action == "HUMAN_REVIEW":
            return self._human_review(ingress, t_start)

        # Step 2: Planning
        plan = self.orchestrator.plan(text, ingress.request_id)
        self._audit.log_planning(
            ingress.request_id, plan.model_used,
            len(plan.subtasks), plan.planning_latency_ms,
        )

        # Step 3+4: Execute subtasks (router + tools)
        subtask_results = self._execute_plan(plan, ingress.request_id)

        # Step 5: Synthesis
        t_synth = time.perf_counter()
        final_response = self.orchestrator.synthesise(plan, subtask_results)
        synth_latency = (time.perf_counter() - t_synth) * 1000
        self._audit.log_synthesis(
            ingress.request_id, plan.model_used,
            _hash(final_response), synth_latency,
        )

        total_latency = (time.perf_counter() - t_start) * 1000

        return AgentResponse(
            request_id=ingress.request_id,
            input_text=text,
            dpi_action=ingress.action,
            plan=plan,
            subtask_results=subtask_results,
            final_response=final_response,
            audit_trail=self._audit.export(),
            total_latency_ms=total_latency,
        )

    def run_audio(self, audio_path: str, dpi_mode: str = "base") -> AgentResponse:
        t_start = time.perf_counter()
        ingress = process_audio_input(audio_path, dpi_mode=dpi_mode)

        if ingress.action == "ERROR":
            return AgentResponse(
                request_id=ingress.request_id,
                input_text="",
                dpi_action="ERROR",
                plan=None,
                subtask_results=[],
                final_response="",
                audit_trail={},
                total_latency_ms=(time.perf_counter() - t_start) * 1000,
                error=ingress.message,
            )

        # Delegate to text pipeline with transcript
        # (rebuild audit with same request_id)
        self._audit.log_ingress(
            ingress.request_id, ingress.text,
            ingress.action, ingress.rule,
        )

        if ingress.action == "DENY":
            return self._denied(ingress, t_start)

        if ingress.action == "HUMAN_REVIEW":
            return self._human_review(ingress, t_start)

        plan = self.orchestrator.plan(ingress.text, ingress.request_id)
        self._audit.log_planning(
            ingress.request_id, plan.model_used,
            len(plan.subtasks), plan.planning_latency_ms,
        )

        subtask_results = self._execute_plan(plan, ingress.request_id)

        t_synth = time.perf_counter()
        final_response = self.orchestrator.synthesise(plan, subtask_results)
        synth_latency = (time.perf_counter() - t_synth) * 1000
        self._audit.log_synthesis(
            ingress.request_id, plan.model_used,
            _hash(final_response), synth_latency,
        )

        total_latency = (time.perf_counter() - t_start) * 1000

        return AgentResponse(
            request_id=ingress.request_id,
            input_text=ingress.text,
            dpi_action=ingress.action,
            plan=plan,
            subtask_results=subtask_results,
            final_response=final_response,
            audit_trail=self._audit.export(),
            total_latency_ms=total_latency,
        )

    def _execute_plan(self, plan: ExecutionPlan, request_id: str) -> list[dict]:
        results: dict[str, dict] = {}

        for subtask in plan.subtasks:
            # Gather context from dependencies
            context_parts = []
            for dep_id in subtask.depends_on:
                if dep_id in results:
                    context_parts.append(results[dep_id].get("output", ""))
            context = "\n".join(context_parts)

            # Tool execution (if applicable)
            tool_output = ""
            if subtask.tool and subtask.tool != "none":
                tool_result = execute_tool(subtask.tool, subtask.description)
                self._audit.log_tool(
                    request_id, subtask.tool,
                    _hash(subtask.description),
                    tool_result.success,
                    tool_result.latency_ms,
                )
                if tool_result.success:
                    import json as _json
                    tool_output = _json.dumps(tool_result.output, ensure_ascii=False)
                    context = f"{context}\nTool output: {tool_output}"

            # Model inference via Featherless
            router_result = self.router.route(
                subtask.id,
                subtask.description,
                subtask.task_type,
                context=context,
            )

            self._audit.log_subtask(
                request_id,
                subtask.id,
                subtask.task_type,
                subtask.tool or "none",
                router_result.model_display,
                _hash(router_result.output),
                router_result.latency_ms,
            )

            result = {
                "subtask_id": subtask.id,
                "description": subtask.description,
                "task_type": subtask.task_type,
                "tool": subtask.tool,
                "model": router_result.model_display,
                "tool_output": tool_output,
                "output": router_result.output,
                "latency_ms": router_result.latency_ms,
                "tokens_used": router_result.tokens_used,
            }
            results[subtask.id] = result

        return list(results.values())

    def _denied(self, ingress: IngressResult, t_start: float) -> AgentResponse:
        total_ms = (time.perf_counter() - t_start) * 1000
        return AgentResponse(
            request_id=ingress.request_id,
            input_text=ingress.text,
            dpi_action="DENY",
            plan=None,
            subtask_results=[],
            final_response=(
                f"Request blocked by SOUF AI DPI governance layer.\n"
                f"Rule: {ingress.rule}\n"
                f"Reason: {ingress.message}"
            ),
            audit_trail=self._audit.export(),
            total_latency_ms=total_ms,
        )

    def _human_review(self, ingress: IngressResult, t_start: float) -> AgentResponse:
        self._audit.log_human_review(ingress.request_id, ingress.rule)
        review = self.orchestrator.escalate_to_human_review(
            ingress.text, ingress.request_id, ingress.rule
        )
        total_ms = (time.perf_counter() - t_start) * 1000
        return AgentResponse(
            request_id=ingress.request_id,
            input_text=ingress.text,
            dpi_action="HUMAN_REVIEW",
            plan=None,
            subtask_results=[],
            final_response=review,
            audit_trail=self._audit.export(),
            total_latency_ms=total_ms,
            human_review_requested=True,
        )
