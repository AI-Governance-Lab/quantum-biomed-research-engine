"""Pharmaceutical & Quantum R&D Clinical Study Grant FinOps Controller.

SQLite-backed budget controller dedicated exclusively to Life Sciences R&D:
- Tracks token usage and USD spend per `clinical_study_id` across Clinical Protocol
  Synthesis, 3x Multi-Judge GxP Evaluation, and Hybrid Quantum VQE Molecular Screening.
- Enforces hard R&D grant caps (raises BudgetExceededError -> HTTP 402/429).
- Generates Chargeback/Showback analytics comparing Sovereign LiteLLM + Spot GPU NIM
  economics (from `nvidia-nim-enterprise-patterns`) against uncalibrated proprietary API spend.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from src.config import EngineSettings, get_settings
from src.schemas import StudyFinOpsReport


class StudyBudgetExceededError(Exception):
    """Raised when a clinical study grant lacks sufficient remaining USD budget."""

    def __init__(self, clinical_study_id: str, requested_usd: float, remaining_usd: float) -> None:
        self.clinical_study_id = clinical_study_id
        self.requested_usd = requested_usd
        self.remaining_usd = remaining_usd
        super().__init__(
            f"Clinical study grant '{clinical_study_id}' exceeded hard FinOps cap: "
            f"required ${requested_usd:.4f} USD, remaining ${remaining_usd:.4f} USD."
        )


class ClinicalStudyBudgetController:
    """SQLite-persisted FinOps controller for Pharmaceutical & Quantum R&D grants."""

    def __init__(self, db_path: Optional[str] = None, settings: Optional[EngineSettings] = None) -> None:
        self.settings = settings or get_settings()
        self.db_path = db_path or self.settings.finops_budget_db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS clinical_study_budgets (
                    clinical_study_id TEXT PRIMARY KEY,
                    allocated_budget_usd REAL NOT NULL,
                    total_spent_usd REAL NOT NULL DEFAULT 0.0,
                    clinical_synthesis_runs INTEGER NOT NULL DEFAULT 0,
                    quantum_screening_runs INTEGER NOT NULL DEFAULT 0,
                    total_prompt_tokens INTEGER NOT NULL DEFAULT 0,
                    total_completion_tokens INTEGER NOT NULL DEFAULT 0,
                    clinical_ai_spend_usd REAL NOT NULL DEFAULT 0.0,
                    quantum_vqe_spend_usd REAL NOT NULL DEFAULT 0.0,
                    updated_at_utc TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def ensure_study_exists(
        self, clinical_study_id: str, allocated_budget_usd: Optional[float] = None
    ) -> Dict[str, Any]:
        """Ensure a study grant record exists; optionally initialize or update its cap."""
        now_utc = datetime.now(timezone.utc).isoformat()
        default_cap = (
            float(allocated_budget_usd)
            if allocated_budget_usd is not None
            else self.settings.default_study_grant_budget_usd
        )
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM clinical_study_budgets WHERE clinical_study_id = ?",
                (clinical_study_id,),
            ).fetchone()
            if row is None:
                conn.execute(
                    """
                    INSERT INTO clinical_study_budgets (
                        clinical_study_id, allocated_budget_usd, updated_at_utc
                    ) VALUES (?, ?, ?)
                    """,
                    (clinical_study_id, default_cap, now_utc),
                )
                conn.commit()
            elif allocated_budget_usd is not None:
                conn.execute(
                    """
                    UPDATE clinical_study_budgets
                    SET allocated_budget_usd = ?, updated_at_utc = ?
                    WHERE clinical_study_id = ?
                    """,
                    (float(allocated_budget_usd), now_utc, clinical_study_id),
                )
                conn.commit()
            updated = conn.execute(
                "SELECT * FROM clinical_study_budgets WHERE clinical_study_id = ?",
                (clinical_study_id,),
            ).fetchone()
            return dict(updated)

    def estimate_clinical_synthesis_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Compute USD cost for clinical synthesis + 3x GxP multi-judge evaluation."""
        total_tokens = max(1, prompt_tokens + completion_tokens)
        synth_cost = (total_tokens / 1000.0) * self.settings.synthesis_cost_per_1k_tokens_usd
        judge_cost = (total_tokens / 1000.0) * self.settings.multi_judge_cost_per_1k_tokens_usd
        return round(max(0.0025, synth_cost + judge_cost), 6)

    def estimate_quantum_screening_cost(self, num_qubits: int, circuit_depth: int) -> float:
        """Compute USD cost for in-silico VQE molecular screening based on qubit-depth volume."""
        base = self.settings.quantum_screen_base_cost_usd
        volume_cost = (num_qubits * circuit_depth) * self.settings.quantum_cost_per_qubit_depth_usd
        return round(base + volume_cost, 6)


    def check_and_charge_clinical(
        self,
        clinical_study_id: str,
        prompt_tokens: int,
        completion_tokens: int,
        allocated_budget_usd: Optional[float] = None,
    ) -> Tuple[float, float]:
        """Verify study budget and record token + USD spend for a clinical synthesis run."""
        record = self.ensure_study_exists(clinical_study_id, allocated_budget_usd)
        tx_cost = self.estimate_clinical_synthesis_cost(prompt_tokens, completion_tokens)
        remaining = float(record["allocated_budget_usd"]) - float(record["total_spent_usd"])
        if tx_cost > remaining + 1e-9:
            raise StudyBudgetExceededError(clinical_study_id, tx_cost, max(0.0, remaining))

        now_utc = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE clinical_study_budgets
                SET total_spent_usd = ROUND(total_spent_usd + ?, 6),
                    clinical_synthesis_runs = clinical_synthesis_runs + 1,
                    total_prompt_tokens = total_prompt_tokens + ?,
                    total_completion_tokens = total_completion_tokens + ?,
                    clinical_ai_spend_usd = ROUND(clinical_ai_spend_usd + ?, 6),
                    updated_at_utc = ?
                WHERE clinical_study_id = ?
                """,
                (tx_cost, prompt_tokens, completion_tokens, tx_cost, now_utc, clinical_study_id),
            )
            conn.commit()
            updated = conn.execute(
                "SELECT * FROM clinical_study_budgets WHERE clinical_study_id = ?",
                (clinical_study_id,),
            ).fetchone()
            new_remaining = round(
                max(0.0, float(updated["allocated_budget_usd"]) - float(updated["total_spent_usd"])), 6
            )
            return tx_cost, new_remaining

    def check_and_charge_quantum(
        self,
        clinical_study_id: str,
        num_qubits: int,
        circuit_depth: int,
        allocated_budget_usd: Optional[float] = None,
    ) -> Tuple[float, float]:
        """Verify study budget and record USD spend for a quantum molecular screening run."""
        record = self.ensure_study_exists(clinical_study_id, allocated_budget_usd)
        tx_cost = self.estimate_quantum_screening_cost(num_qubits, circuit_depth)
        remaining = float(record["allocated_budget_usd"]) - float(record["total_spent_usd"])
        if tx_cost > remaining + 1e-9:
            raise StudyBudgetExceededError(clinical_study_id, tx_cost, max(0.0, remaining))

        now_utc = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE clinical_study_budgets
                SET total_spent_usd = ROUND(total_spent_usd + ?, 6),
                    quantum_screening_runs = quantum_screening_runs + 1,
                    quantum_vqe_spend_usd = ROUND(quantum_vqe_spend_usd + ?, 6),
                    updated_at_utc = ?
                WHERE clinical_study_id = ?
                """,
                (tx_cost, tx_cost, now_utc, clinical_study_id),
            )
            conn.commit()
            updated = conn.execute(
                "SELECT * FROM clinical_study_budgets WHERE clinical_study_id = ?",
                (clinical_study_id,),
            ).fetchone()
            new_remaining = round(
                max(0.0, float(updated["allocated_budget_usd"]) - float(updated["total_spent_usd"])), 6
            )
            return tx_cost, new_remaining


    def get_study_report(self, clinical_study_id: str) -> StudyFinOpsReport:
        """Build a Pharmaceutical & Quantum R&D Chargeback/Showback report for a study."""
        row = self.ensure_study_exists(clinical_study_id)
        allocated = float(row["allocated_budget_usd"])
        spent = round(float(row["total_spent_usd"]), 6)
        remaining = round(max(0.0, allocated - spent), 6)
        utilization_pct = round((spent / allocated) * 100.0, 2) if allocated > 0 else 100.0

        synth_runs = int(row["clinical_synthesis_runs"])
        quantum_runs = int(row["quantum_screening_runs"])
        clinical_spend = round(float(row["clinical_ai_spend_usd"]), 6)
        quantum_spend = round(float(row["quantum_vqe_spend_usd"]), 6)

        avg_synth = round(clinical_spend / synth_runs, 6) if synth_runs > 0 else 0.0
        avg_quantum = round(quantum_spend / quantum_runs, 6) if quantum_runs > 0 else 0.0

        if remaining <= 0.0025:
            status = "EXHAUSTED_HARD_CAP"
        elif utilization_pct >= 80.0:
            status = "WARNING_NEAR_CAP"
        else:
            status = "HEALTHY"

        spot_savings_pct = round(
            (1.0 - (self.settings.nim_l4_spot_hourly_usd / self.settings.nim_l4_ondemand_hourly_usd)) * 100.0,
            1,
        )
        proprietary_equiv = round(spent * self.settings.cloud_proprietary_api_equivalent_multiplier, 4)

        return StudyFinOpsReport(
            clinical_study_id=clinical_study_id,
            allocated_budget_usd=allocated,
            total_spent_usd=spent,
            remaining_budget_usd=remaining,
            budget_utilization_pct=utilization_pct,
            clinical_synthesis_runs=synth_runs,
            quantum_screening_runs=quantum_runs,
            total_prompt_tokens=int(row["total_prompt_tokens"]),
            total_completion_tokens=int(row["total_completion_tokens"]),
            clinical_ai_spend_usd=clinical_spend,
            quantum_vqe_spend_usd=quantum_spend,
            avg_cost_per_clinical_synthesis_usd=avg_synth,
            avg_cost_per_screened_molecule_usd=avg_quantum,
            budget_status=status,
            gpu_infrastructure_comparison={
                "nim_l4_spot_hourly_usd": self.settings.nim_l4_spot_hourly_usd,
                "nim_l4_ondemand_hourly_usd": self.settings.nim_l4_ondemand_hourly_usd,
                "ephemeral_spot_gpu_savings_pct": spot_savings_pct,
                "proprietary_uncalibrated_api_equivalent_usd": proprietary_equiv,
                "estimated_grant_savings_usd": round(max(0.0, proprietary_equiv - spent), 4),
                "reference_architecture": "nvidia-nim-enterprise-patterns + private-enterprise-ai-hub",
            },
        )

    def list_studies(self) -> List[StudyFinOpsReport]:
        """Return FinOps reports for all tracked clinical studies."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT clinical_study_id FROM clinical_study_budgets ORDER BY updated_at_utc DESC"
            ).fetchall()
        return [self.get_study_report(r["clinical_study_id"]) for r in rows]
