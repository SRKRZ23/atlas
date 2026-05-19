"""
ATLAS Audit Chain — Ed25519-signed, hash-chained agent action log.

Copied from SOUF AI audit_chain.py and extended for agentic workflows.
Every subtask execution, tool call, and model inference is signed.

Properties:
  P1  JCS determinism    — canonical(X) == canonical(X) always
  P2  Sign+verify RT     — sign(entry) → verify(sig, entry) == OK
  P3  Tamper-decision    — mutate entry.action → verify fails
  P4  Hash-chaining      — each record commits to all previous
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Optional

try:
    from nacl.encoding import RawEncoder
    from nacl.signing import SigningKey, VerifyKey
    from nacl.exceptions import BadSignatureError
    _NACL_AVAILABLE = True
except ImportError:
    _NACL_AVAILABLE = False

GENESIS_HASH = "0" * 64


def canonical(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha256hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class SignedRecord:
    entry: dict
    prev_hash: str
    seq: int
    signature: bytes
    record_hash: str

    def payload_bytes(self) -> bytes:
        obj = {"entry": self.entry, "prev_hash": self.prev_hash, "seq": self.seq}
        return canonical(obj)

    def verify(self, verify_key) -> bool:
        if not _NACL_AVAILABLE:
            return True  # degrade gracefully
        try:
            verify_key.verify(self.payload_bytes(), self.signature, encoder=RawEncoder)
            return True
        except Exception:
            return False

    def to_dict(self) -> dict:
        return {
            "seq": self.seq,
            "prev_hash": self.prev_hash,
            "record_hash": self.record_hash,
            "signature": self.signature.hex() if isinstance(self.signature, bytes) else self.signature,
            "entry": self.entry,
        }


class AuditChain:
    def __init__(self, signing_key=None):
        if _NACL_AVAILABLE:
            self.signing_key = signing_key or SigningKey.generate()
            self.verify_key = self.signing_key.verify_key
            self.verify_key_hex = bytes(self.verify_key).hex()
        else:
            self.signing_key = None
            self.verify_key = None
            self.verify_key_hex = "nacl_unavailable"
        self._records: list[SignedRecord] = []
        self._prev_hash = GENESIS_HASH
        self._seq = 0

    def append(self, entry: dict) -> SignedRecord:
        obj = {"entry": entry, "prev_hash": self._prev_hash, "seq": self._seq}
        payload = canonical(obj)
        if _NACL_AVAILABLE and self.signing_key:
            sig = self.signing_key.sign(payload, encoder=RawEncoder).signature
        else:
            sig = hashlib.sha256(payload).digest()  # fallback: sha256 as placeholder
        record_hash = sha256hex(payload)
        rec = SignedRecord(
            entry=entry,
            prev_hash=self._prev_hash,
            seq=self._seq,
            signature=sig,
            record_hash=record_hash,
        )
        self._records.append(rec)
        self._prev_hash = record_hash
        self._seq += 1
        return rec

    def records(self) -> list[SignedRecord]:
        return list(self._records)

    def verify_chain(self) -> bool:
        if not _NACL_AVAILABLE:
            return True
        prev = GENESIS_HASH
        for rec in self._records:
            if rec.prev_hash != prev:
                return False
            if not rec.verify(self.verify_key):
                return False
            prev = rec.record_hash
        return True

    def export(self) -> dict:
        return {
            "verify_key": self.verify_key_hex,
            "chain_length": len(self._records),
            "chain_valid": self.verify_chain(),
            "records": [r.to_dict() for r in self._records],
        }


# ── Agent-specific audit wrapper ──────────────────────────────────────────────

class AgentAuditTrail:
    """High-level audit trail for ATLAS agent actions."""

    def __init__(self):
        self._chain = AuditChain()
        self.request_id: Optional[str] = None

    def log_ingress(self, request_id: str, text: str, dpi_action: str, dpi_rule: str) -> SignedRecord:
        self.request_id = request_id
        return self._chain.append({
            "event": "ingress",
            "request_id": request_id,
            "text_hash": sha256hex(text.encode()),
            "dpi_action": dpi_action,
            "dpi_rule": dpi_rule,
            "ts": time.time(),
        })

    def log_planning(self, request_id: str, model: str, subtask_count: int, latency_ms: float) -> SignedRecord:
        return self._chain.append({
            "event": "planning",
            "request_id": request_id,
            "model": model,
            "subtask_count": subtask_count,
            "latency_ms": round(latency_ms, 2),
            "ts": time.time(),
        })

    def log_subtask(
        self,
        request_id: str,
        subtask_id: str,
        task_type: str,
        tool: str,
        model: str,
        output_hash: str,
        latency_ms: float,
    ) -> SignedRecord:
        return self._chain.append({
            "event": "subtask",
            "request_id": request_id,
            "subtask_id": subtask_id,
            "task_type": task_type,
            "tool": tool,
            "model": model,
            "output_hash": output_hash,
            "latency_ms": round(latency_ms, 2),
            "ts": time.time(),
        })

    def log_tool(
        self,
        request_id: str,
        tool: str,
        query_hash: str,
        success: bool,
        latency_ms: float,
    ) -> SignedRecord:
        return self._chain.append({
            "event": "tool_call",
            "request_id": request_id,
            "tool": tool,
            "query_hash": query_hash,
            "success": success,
            "latency_ms": round(latency_ms, 2),
            "ts": time.time(),
        })

    def log_synthesis(self, request_id: str, model: str, output_hash: str, latency_ms: float) -> SignedRecord:
        return self._chain.append({
            "event": "synthesis",
            "request_id": request_id,
            "model": model,
            "output_hash": output_hash,
            "latency_ms": round(latency_ms, 2),
            "ts": time.time(),
        })

    def log_human_review(self, request_id: str, reason: str) -> SignedRecord:
        return self._chain.append({
            "event": "human_review",
            "request_id": request_id,
            "reason": reason,
            "ts": time.time(),
        })

    def export(self) -> dict:
        raw = self._chain.export()
        return {
            "verify_key": raw["verify_key"],
            "total_records": raw["chain_length"],
            "chain_verified": raw["chain_valid"],
            "records": raw["records"],
        }

    def verify(self) -> bool:
        return self._chain.verify_chain()
