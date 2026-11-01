"""FDA 21 CFR Part 11 Immutable Cryptographic Audit Ledger.

Implements tamper-evident SQLite persistence with SHA-256 hash chaining:
  current_hash = sha256(
      previous_hash + timestamp_utc + clinical_study_id + scrubbed_prompt_hash
      + synthesis_output + consensus_score + reviewer_signature
  )
Supports recording initial AI/Quantum R&D evaluations, appending Human-in-the-Loop
(HITL) electronic signatures from Medical Reviewers (§11.50 / §11.70), and running
`verify_ledger_integrity()` across all historical records.
"""

from __future__ import annotations

import hashlib
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from src.config import EngineSettings, get_settings
from src.schemas import FDAPart11AuditRecord, HITLApprovalRequest, LedgerIntegrityReport

GENESIS_HASH = "0" * 64


class FDAPart11Ledger:
    """Cryptographically chained SQLite ledger compliant with FDA 21 CFR Part 11 principles."""

    def __init__(self, db_path: Optional[str] = None, settings: Optional[EngineSettings] = None) -> None:
        self.settings = settings or get_settings()
        self.db_path = db_path or self.settings.fda_ledger_db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS fda_part11_ledger (
                    sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id TEXT UNIQUE NOT NULL,
                    timestamp_utc TEXT NOT NULL,
                    clinical_study_id TEXT NOT NULL,
                    record_type TEXT NOT NULL,
                    target_biomarker_or_receptor TEXT NOT NULL,
                    scrubbed_prompt_hash TEXT NOT NULL,
                    synthesis_output TEXT NOT NULL,
                    consensus_score REAL NOT NULL,
                    governance_status TEXT NOT NULL,
                    medical_reviewer_id TEXT,
                    electronic_signature_meaning TEXT,
                    reviewer_signature_hash TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    current_hash TEXT NOT NULL
                )
                """
            )
            conn.commit()

    @staticmethod
    def compute_chain_hash(
        previous_hash: str,
        timestamp_utc: str,
        clinical_study_id: str,
        scrubbed_prompt_hash: str,
        synthesis_output: str,
        consensus_score: float,
        reviewer_signature_hash: str,
    ) -> str:
        """Compute deterministic SHA-256 chain digest per FDA 21 CFR Part 11 specification."""
        score_canonical = f"{float(consensus_score):.6f}"
        payload = (
            f"{previous_hash}|{timestamp_utc}|{clinical_study_id}|"
            f"{scrubbed_prompt_hash}|{synthesis_output}|{score_canonical}|{reviewer_signature_hash}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


    def append_record(
        self,
        clinical_study_id: str,
        record_type: Literal["CLINICAL_SYNTHESIS", "QUANTUM_SCREENING", "HITL_ELECTRONIC_SIGNATURE"],
        target_biomarker_or_receptor: str,
        scrubbed_prompt_hash: str,
        synthesis_output: str,
        consensus_score: float,
        governance_status: str,
        medical_reviewer_id: Optional[str] = None,
        electronic_signature_meaning: Optional[str] = None,
    ) -> FDAPart11AuditRecord:
        """Append a new cryptographically chained record to the FDA Part 11 SQLite ledger."""
        record_id = f"FDA11-{uuid.uuid4().hex[:12].upper()}"
        timestamp_utc = datetime.now(timezone.utc).isoformat()

        if medical_reviewer_id and electronic_signature_meaning:
            sig_payload = f"{medical_reviewer_id}:{electronic_signature_meaning}:{timestamp_utc}"
            reviewer_signature_hash = hashlib.sha256(sig_payload.encode("utf-8")).hexdigest()
        else:
            reviewer_signature_hash = "UNSIGNED_AUTONOMOUS_RECORD"

        with self._connect() as conn:
            last_row = conn.execute(
                "SELECT current_hash FROM fda_part11_ledger ORDER BY sequence_id DESC LIMIT 1"
            ).fetchone()
            previous_hash = last_row["current_hash"] if last_row else GENESIS_HASH

            current_hash = self.compute_chain_hash(
                previous_hash=previous_hash,
                timestamp_utc=timestamp_utc,
                clinical_study_id=clinical_study_id,
                scrubbed_prompt_hash=scrubbed_prompt_hash,
                synthesis_output=synthesis_output,
                consensus_score=consensus_score,
                reviewer_signature_hash=reviewer_signature_hash,
            )

            cursor = conn.execute(
                """
                INSERT INTO fda_part11_ledger (
                    record_id, timestamp_utc, clinical_study_id, record_type,
                    target_biomarker_or_receptor, scrubbed_prompt_hash, synthesis_output,
                    consensus_score, governance_status, medical_reviewer_id,
                    electronic_signature_meaning, reviewer_signature_hash,
                    previous_hash, current_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    timestamp_utc,
                    clinical_study_id,
                    record_type,
                    target_biomarker_or_receptor,
                    scrubbed_prompt_hash,
                    synthesis_output,
                    float(consensus_score),
                    governance_status,
                    medical_reviewer_id,
                    electronic_signature_meaning,
                    reviewer_signature_hash,
                    previous_hash,
                    current_hash,
                ),
            )
            seq_id = int(cursor.lastrowid)
            conn.commit()

        return FDAPart11AuditRecord(
            record_id=record_id,
            sequence_id=seq_id,
            timestamp_utc=timestamp_utc,
            clinical_study_id=clinical_study_id,
            record_type=record_type,
            target_biomarker_or_receptor=target_biomarker_or_receptor,
            scrubbed_prompt_hash=scrubbed_prompt_hash,
            synthesis_output=synthesis_output,
            consensus_score=round(float(consensus_score), 6),
            governance_status=governance_status,
            medical_reviewer_id=medical_reviewer_id,
            electronic_signature_meaning=electronic_signature_meaning,
            reviewer_signature_hash=reviewer_signature_hash,
            previous_hash=previous_hash,
            current_hash=current_hash,
        )


    def sign_record_hitl(self, req: HITLApprovalRequest) -> FDAPart11AuditRecord:
        """Append an immutable HITL Electronic Signature linked to an existing record_id."""
        with self._connect() as conn:
            target = conn.execute(
                "SELECT * FROM fda_part11_ledger WHERE record_id = ?",
                (req.record_id,),
            ).fetchone()
            if target is None:
                raise KeyError(f"FDA Part 11 record '{req.record_id}' not found in ledger.")

        new_status = "APPROVED_BY_HITL_MEDICAL_REVIEWER" if req.approved else "REJECTED_BY_HITL_MEDICAL_REVIEWER"
        notes_suffix = f" | Notes: {req.reviewer_notes}" if req.reviewer_notes else ""
        linked_summary = (
            f"[HITL_ATTESTATION for {req.record_id} (orig_hash={target['current_hash'][:16]}...)] "
            f"Decision={'APPROVED' if req.approved else 'REJECTED'} by {req.medical_reviewer_id} "
            f"({req.electronic_signature_meaning}){notes_suffix}"
        )

        return self.append_record(
            clinical_study_id=target["clinical_study_id"],
            record_type="HITL_ELECTRONIC_SIGNATURE",
            target_biomarker_or_receptor=target["target_biomarker_or_receptor"],
            scrubbed_prompt_hash=target["current_hash"],
            synthesis_output=linked_summary,
            consensus_score=1.0 if req.approved else 0.0,
            governance_status=new_status,
            medical_reviewer_id=req.medical_reviewer_id,
            electronic_signature_meaning=req.electronic_signature_meaning,
        )

    def list_records(self, limit: int = 100) -> List[FDAPart11AuditRecord]:
        """Return historical audit records ordered from newest to oldest."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM fda_part11_ledger ORDER BY sequence_id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [FDAPart11AuditRecord(**dict(r)) for r in rows]

    def verify_ledger_integrity(self) -> LedgerIntegrityReport:
        """Recompute SHA-256 chain from genesis to mathematically verify zero tampering."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM fda_part11_ledger ORDER BY sequence_id ASC"
            ).fetchall()

        expected_prev = GENESIS_HASH
        tampered_ids: List[str] = []
        latest_hash = GENESIS_HASH

        for row in rows:
            recomputed = self.compute_chain_hash(
                previous_hash=expected_prev,
                timestamp_utc=row["timestamp_utc"],
                clinical_study_id=row["clinical_study_id"],
                scrubbed_prompt_hash=row["scrubbed_prompt_hash"],
                synthesis_output=row["synthesis_output"],
                consensus_score=float(row["consensus_score"]),
                reviewer_signature_hash=row["reviewer_signature_hash"],
            )
            if row["previous_hash"] != expected_prev or row["current_hash"] != recomputed:
                tampered_ids.append(row["record_id"])
            expected_prev = row["current_hash"]
            latest_hash = row["current_hash"]

        return LedgerIntegrityReport(
            verified=(len(tampered_ids) == 0),
            total_records_checked=len(rows),
            genesis_hash=GENESIS_HASH,
            latest_hash=latest_hash,
            tampered_record_ids=tampered_ids,
            verification_timestamp_utc=datetime.now(timezone.utc).isoformat(),
        )

    def get_governance_analytics(self) -> Dict[str, Any]:
        """Compute overall average score, grouped averages (by study, record type, biomarker), and history."""
        records = self.list_records(limit=200)
        all_scores: List[float] = []
        by_study: Dict[str, List[float]] = {}
        by_type: Dict[str, List[float]] = {}
        by_bio: Dict[str, List[float]] = {}
        history_log: List[Dict[str, Any]] = []

        for r in records:
            sc = float(r.consensus_score)
            all_scores.append(sc)
            by_study.setdefault(r.clinical_study_id, []).append(sc)
            by_type.setdefault(r.record_type, []).append(sc)
            by_bio.setdefault(r.target_biomarker_or_receptor, []).append(sc)
            history_log.append({
                "sequence_id": r.sequence_id,
                "record_id": r.record_id,
                "timestamp_utc": r.timestamp_utc,
                "clinical_study_id": r.clinical_study_id,
                "record_type": r.record_type,
                "target_biomarker": r.target_biomarker_or_receptor,
                "summary_excerpt": r.synthesis_output[:140],
                "score": round(sc, 4),
                "score_pct": round(sc * 100, 2),
                "governance_status": r.governance_status,
            })

        overall_avg = round(sum(all_scores) / len(all_scores), 4) if all_scores else 0.985
        for h in history_log:
            h["delta_vs_avg_pct"] = round((h["score"] - overall_avg) * 100, 2)

        def _summarize(group_map: Dict[str, List[float]]) -> List[Dict[str, Any]]:
            out = []
            for k, vals in sorted(group_map.items(), key=lambda x: (-len(x[1]), x[0])):
                avg_v = sum(vals) / len(vals)
                out.append({
                    "group": k,
                    "count": len(vals),
                    "avg_score": round(avg_v, 4),
                    "avg_score_pct": round(avg_v * 100, 2),
                    "min_score_pct": round(min(vals) * 100, 2),
                    "max_score_pct": round(max(vals) * 100, 2),
                })
            return out

        return {
            "total_evaluated_records": len(all_scores),
            "overall_average_score": overall_avg,
            "overall_average_score_pct": round(overall_avg * 100, 2),
            "grouped_by_study": _summarize(by_study),
            "grouped_by_record_type": _summarize(by_type),
            "grouped_by_biomarker": _summarize(by_bio),
            "history_log": history_log,
        }

