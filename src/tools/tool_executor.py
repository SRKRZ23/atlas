"""
ATLAS Tool Execution Layer.

Tools:
  - search    : web search via DuckDuckGo (no API key required)
  - database  : read-only sandbox DB queries
  - kraken    : Kraken market data + order book
  - vultr     : Vultr cloud infrastructure queries
"""
from __future__ import annotations

import os
import json
import logging
import time
from dataclasses import dataclass
from typing import Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    tool: str
    query: str
    output: Any
    latency_ms: float
    success: bool
    error: str = ""


# ── Search ────────────────────────────────────────────────────────────────────

def _tool_search(query: str) -> ToolResult:
    t0 = time.perf_counter()
    try:
        import httpx
        resp = httpx.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_redirect": 1, "no_html": 1},
            timeout=8.0,
        )
        data = resp.json()
        abstract = data.get("Abstract", "")
        related = [r.get("Text", "") for r in data.get("RelatedTopics", [])[:3]]
        output = {"abstract": abstract, "related": related, "source": data.get("AbstractURL", "")}
        latency_ms = (time.perf_counter() - t0) * 1000
        return ToolResult("search", query, output, latency_ms, True)
    except Exception as e:
        latency_ms = (time.perf_counter() - t0) * 1000
        return ToolResult("search", query, {}, latency_ms, False, str(e))


# ── Database (read-only sandbox) ──────────────────────────────────────────────

_MOCK_DB = {
    "users": [
        {"id": 1, "name": "Alice Chen", "dept": "Engineering", "clearance": "L3"},
        {"id": 2, "name": "Bob Kumar", "dept": "Finance", "clearance": "L2"},
    ],
    "transactions": [
        {"id": "TXN-001", "amount": 15000, "currency": "USD", "status": "settled"},
        {"id": "TXN-002", "amount": 8500, "currency": "EUR", "status": "pending"},
    ],
    "policies": [
        {"id": "POL-001", "name": "Data Retention", "version": "2.1", "active": True},
        {"id": "POL-002", "name": "Access Control", "version": "3.0", "active": True},
    ],
}


def _tool_database(query: str) -> ToolResult:
    t0 = time.perf_counter()
    query_lower = query.lower()
    for table in _MOCK_DB:
        if table in query_lower:
            output = {"table": table, "rows": _MOCK_DB[table], "count": len(_MOCK_DB[table])}
            latency_ms = (time.perf_counter() - t0) * 1000
            return ToolResult("database", query, output, latency_ms, True)
    output = {"message": "Query executed", "rows": [], "count": 0}
    latency_ms = (time.perf_counter() - t0) * 1000
    return ToolResult("database", query, output, latency_ms, True)


# ── Kraken market data ────────────────────────────────────────────────────────

def _tool_kraken(query: str) -> ToolResult:
    t0 = time.perf_counter()
    api_key = os.environ.get("KRAKEN_API_KEY", "")

    # Always try public endpoints first (no auth required)
    try:
        import httpx
        query_lower = query.lower()

        # Determine which pair to look up
        pair = "XXBTZUSD"
        if "eth" in query_lower or "ethereum" in query_lower:
            pair = "XETHZUSD"
        elif "sol" in query_lower or "solana" in query_lower:
            pair = "SOLUSD"
        elif "ada" in query_lower or "cardano" in query_lower:
            pair = "ADAUSD"

        resp = httpx.get(
            f"https://api.kraken.com/0/public/Ticker",
            params={"pair": pair},
            timeout=8.0,
        )
        data = resp.json()

        if data.get("error"):
            raise ValueError(data["error"])

        result_data = list(data["result"].values())[0]
        output = {
            "pair": pair,
            "last_price": result_data["c"][0],
            "bid": result_data["b"][0],
            "ask": result_data["a"][0],
            "volume_24h": result_data["v"][1],
            "high_24h": result_data["h"][1],
            "low_24h": result_data["l"][1],
            "source": "Kraken Public API",
        }
        latency_ms = (time.perf_counter() - t0) * 1000
        return ToolResult("kraken", query, output, latency_ms, True)

    except Exception as e:
        logger.warning("Kraken API error: %s — using mock data", e)
        # Fallback mock data
        output = {
            "pair": "XXBTZUSD",
            "last_price": "67842.50",
            "bid": "67840.00",
            "ask": "67845.00",
            "volume_24h": "12543.21",
            "high_24h": "68900.00",
            "low_24h": "66100.00",
            "source": "mock (Kraken unavailable)",
        }
        latency_ms = (time.perf_counter() - t0) * 1000
        return ToolResult("kraken", query, output, latency_ms, True)


# ── Vultr infrastructure ──────────────────────────────────────────────────────

def _tool_vultr(query: str) -> ToolResult:
    t0 = time.perf_counter()
    api_key = os.environ.get("VULTR_API_KEY", "")

    if api_key:
        try:
            import httpx
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            resp = httpx.get(
                "https://api.vultr.com/v2/instances",
                headers=headers,
                timeout=8.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                instances = data.get("instances", [])
                output = {
                    "total_instances": len(instances),
                    "instances": [
                        {
                            "id": i.get("id"),
                            "label": i.get("label"),
                            "status": i.get("status"),
                            "region": i.get("region"),
                            "plan": i.get("plan"),
                            "ram": i.get("ram"),
                            "vcpu_count": i.get("vcpu_count"),
                        }
                        for i in instances[:5]
                    ],
                    "source": "Vultr API",
                }
                latency_ms = (time.perf_counter() - t0) * 1000
                return ToolResult("vultr", query, output, latency_ms, True)
        except Exception as e:
            logger.warning("Vultr API error: %s", e)

    # Mock fallback
    output = {
        "total_instances": 3,
        "instances": [
            {"id": "v-001", "label": "atlas-prod-01", "status": "active", "region": "ewr", "plan": "vc2-4c-8gb", "ram": 8192, "vcpu_count": 4},
            {"id": "v-002", "label": "atlas-worker-01", "status": "active", "region": "lax", "plan": "vc2-2c-4gb", "ram": 4096, "vcpu_count": 2},
            {"id": "v-003", "label": "atlas-db-01", "status": "active", "region": "ewr", "plan": "vc2-4c-8gb", "ram": 8192, "vcpu_count": 4},
        ],
        "source": "mock (Vultr API key not set)" if not api_key else "mock (API error)",
    }
    latency_ms = (time.perf_counter() - t0) * 1000
    return ToolResult("vultr", query, output, latency_ms, True)


# ── Dispatcher ────────────────────────────────────────────────────────────────

_TOOL_MAP = {
    "search":   _tool_search,
    "database": _tool_database,
    "kraken":   _tool_kraken,
    "vultr":    _tool_vultr,
}


def execute_tool(tool: str, query: str) -> ToolResult:
    fn = _TOOL_MAP.get(tool)
    if fn is None:
        return ToolResult(tool, query, {}, 0.0, False, f"Unknown tool: {tool}")
    return fn(query)
