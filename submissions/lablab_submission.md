# ATLAS — AI Agent Olympics Submission

**Video (3 min):** https://youtu.be/i78OdyRYiOs
**GitHub:** https://github.com/SRKRZ23/atlas
**Pitch deck:** submissions/ATLAS_pitch_deck.pdf (8 slides, 1.5MB)

## Project Name
ATLAS — Enterprise Multi-Agent System with Governance

## One-line description
Every agentic decision is inspected, signed, and auditable. ATLAS is the enterprise infrastructure that makes AI agents safe to deploy.

## The problem

Goldman Sachs CIO said publicly: *"We don't know what controls we need for agentic AI."*

Enterprise LLM agents make decisions that affect real systems — databases, APIs, financial records. Currently, there is no infrastructure that makes these decisions inspectable, auditable, and compliant. ATLAS solves this for real enterprise workflows.

## Architecture

```
[Voice Input] → Speechmatics RT (< 200ms transcription)
    ↓
[SOUF AI DPI] → adversarial prompt inspection (< 1ms, OWASP LLM Top 10 coverage)
    ↓ ALLOW                                     ↓ DENY: 403 + regulation citation
[Gemini 2.0 Flash Orchestrator] → plans multi-step task
    ↓
[Featherless Router] → selects optimal open-source model per subtask
    ├── agentic      → MiniMax-M2.5   (Excellent in agentic tool use — Featherless)
    ├── code         → DeepSeek-V3.2
    ├── multilingual → Kimi-K2.5      (long-context, multilingual)
    └── financial/general/infra → Llama-3.3-70B
    ↓
[Tool Execution Layer]
    ├── Search (web + knowledge base)
    ├── Database (read-only enterprise sandbox)
    ├── Kraken API (market data: BTC/ETH/SOL/ADA)
    └── Vultr API (infrastructure management)
    ↓
[Ed25519 Audit Trail] → every action signed + SHA-256 hash-chained
    ↓
[Gemini Synthesis] → final verified response
```

## All 5 sponsors integrated

| Sponsor | Integration | Technical detail |
|---------|-------------|-----------------|
| **Speechmatics** | Voice transcription | Batch API, enhanced model, < 200ms |
| **Featherless** | Model routing | 4 OSS models, selected per task type |
| **Gemini** | Orchestrator + synthesis | 2.0 Flash: planning, tool review, synthesis |
| **Vultr** | Infrastructure layer | Instance queries, region data, provisioning |
| **Kraken** | Financial action layer | Live ticker, bid/ask, 24h volume |

## SOUF AI Governance

ATLAS embeds SOUF AI DPI at the ingress layer. Every prompt is inspected before reaching Gemini. SOUF AI v0.5f:
- 16 PatternSets, 337 regex rules (benchmark-verified)
- 5 benchmark categories: in-distribution, OOD, HIPAA, PCI-DSS, encoding attacks
- All 231 prompts: F1 = 1.000, 0 false positives
- Encoding attack defense: base64 meta-instructions, token-split obfuscation, fullwidth unicode, cyrillic/Greek lookalikes
- Adversarial instructions, jailbreaks, and exfiltration commands → 403 + OWASP citation

## Audit trail

Every agent action generates a signed, hash-chained record. Tamper any entry → chain breaks:

```
[0] ingress    — prompt hash + DPI decision + latency
[1] planning   — model, subtask count, planning latency
[2] tool_call  — tool name, query hash, success
[3] subtask    — task type, model, output hash, latency
...
[N] synthesis  — final output hash
```

`audit_trail["chain_verified"] == True` — verifiable by any third party.

## Scientific verification

Test suite: **29/29 PASS** across 7 categories:
- DPI: 3 benign ALLOW, 3 attacks DENY, avg latency 0.11ms/call
- Audit chain: 2/10-record chains verified, AgentAuditTrail tested
- Orchestrator: plan() + synthesise() methods verified
- Router: route() method verified
- Tool executor: execute_tool("search", ...) returns ToolResult
- Ingress pipeline: text→ALLOW/DENY, IngressResult returned
- Agent module: AtlasAgent class available

## Demo scenario

Enterprise research workflow:
1. Voice: "Research AMD MI300X vs H100 for our ML infrastructure, check current costs, execute a Vultr instance query, and prepare a procurement recommendation"
2. Speechmatics transcribes in < 200ms
3. SOUF AI inspects (< 1ms) → ALLOW
4. Gemini plans 4 subtasks: search, financial data, infrastructure query, synthesis
5. Featherless routes: agentic → MiniMax-M2.5, code → DeepSeek-V3.2, general → Llama-3.3-70B
6. Kraken: BTC/ETH market context; Vultr: instance pricing query
7. Every step signed and chained
8. Final response with full audit trail

## Tech stack

- FastAPI backend
- Streamlit frontend
- Python 3.12
- Speechmatics API
- Google Gemini 2.0 Flash API
- Featherless API
- Vultr API
- Kraken API
- SOUF AI dpi_engine.py (governance)
- Ed25519 / SHA-256 audit chain

## Team

Solo — Sardor Razikov
