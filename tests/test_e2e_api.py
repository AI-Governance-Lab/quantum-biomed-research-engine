"""End-to-End Test Suite for the Quantum BioMed Research Engine.

Validates:
1. Kubernetes Liveness/Readiness probes & React 18 Workbench UI serving
2. Deterministic HIPAA / GDPR PHI Scrubber redaction across all identifier classes
3. Clinical Trial Synthesis + 3x Concurrent GxP Multi-Judge Consensus (Autonomous & HITL escalation)
4. Hybrid Quantum-AI VQE Molecular Screening (statevector energy, binding affinity, circuit depth)
5. FDA 21 CFR Part 11 Human-in-the-Loop (HITL) Electronic Signature attestation
6. Clinical Study & Quantum R&D Grant FinOps tracking + HTTP 402 hard budget cap enforcement
7. Cryptographic SHA-256 hash-chain verification & SQLite tamper detection
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Provide an isolated FastAPI TestClient backed by temporary SQLite ledgers."""
    fda_db = tmp_path / "test_fda_part11_ledger.db"
    finops_db = tmp_path / "test_clinical_finops.db"
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("FDA_LEDGER_DB_PATH", str(fda_db))
    monkeypatch.setenv("FINOPS_BUDGET_DB_PATH", str(finops_db))
    monkeypatch.setenv("LLM_LIVE_MODE", "false")
    monkeypatch.setenv("GXP_CONSENSUS_THRESHOLD", "0.95")
    monkeypatch.setenv("DEFAULT_STUDY_GRANT_BUDGET_USD", "2500.00")
    return TestClient(app)


def test_health_probes_and_workbench_ui(client: TestClient) -> None:
    """Verify Kubernetes /healthz, /readyz, /v1/config/runtime and React 18 UI."""
    h_res = client.get("/healthz")
    assert h_res.status_code == 200
    assert h_res.json()["status"] == "ok"

    r_res = client.get("/readyz")
    assert r_res.status_code == 200
    assert r_res.json()["ledger_verified"] is True

    cfg_res = client.get("/v1/config/runtime")
    assert cfg_res.status_code == 200
    assert cfg_res.json()["gxp_consensus_threshold"] == 0.95

    mod_res = client.get("/v1/models")
    assert mod_res.status_code == 200
    assert len(mod_res.json()["models"]) >= 5

    ui_res = client.get("/")
    assert ui_res.status_code == 200
    assert "Quantum BioMed Research" in ui_res.text
    assert "Venus Quantum App (:30088)" in ui_res.text


def test_phi_redaction_and_autonomous_clinical_synthesis(client: TestClient) -> None:
    """Verify HIPAA PHI scrubbing, paragraph citations [CIT-Px], and 3x judge consensus >= 0.95."""
    payload = {
        "clinical_study_id": "STUDY-ONCO-KRAS-2026",
        "target_biomarker": "KRAS-G12C",
        "protocol_text": (
            "Patient Name: Johnathan Miller, DOB: 1968-04-19, MRN: ONC-884920, "
            "SSN: 412-88-9021, Email: j.miller68@clinical.org, Phone: +1 (617) 555-0199. "
            "Cohort A evaluated oral covalent KRAS-G12C inhibition. Safety logs noted "
            "Grade 2 nausea, mild diarrhea, fatigue, and elevated ALT/AST transaminases. "
            "Patients with hepatic impairment or strong CYP3A4 inducers were excluded."
        ),
    }
    res = client.post("/v1/clinical/synthesize", json=payload)
    assert res.status_code == 200
    data = res.json()

    # 1. Verify PHI redaction
    privacy = data["privacy_audit"]
    assert privacy["total_redactions"] >= 5
    scrubbed = privacy["scrubbed_text"]
    assert "Johnathan Miller" not in scrubbed
    assert "412-88-9021" not in scrubbed
    assert "ONC-884920" not in scrubbed
    assert "[REDACTED_PATIENT_ID]" in scrubbed
    assert "[REDACTED_SSN_CNP]" in scrubbed
    assert "[REDACTED_MRN]" in scrubbed

    # 2. Verify clinical synthesis & citations
    synth = data["synthesis"]
    assert "[CIT-P1]" in synth["executive_clinical_synthesis"]
    assert "[CIT-P2]" in synth["executive_clinical_synthesis"]
    assert len(synth["extracted_adverse_events"]) >= 3

    # 3. Verify 3x GxP multi-judge consensus
    consensus = data["consensus_evaluation"]
    assert len(consensus["judges"]) == 3
    assert consensus["consensus_score"] >= 0.95
    assert consensus["governance_status"] == "APPROVED_AUTONOMOUS"
    assert data["fda_part11_record"]["record_id"].startswith("FDA11-")




def test_high_risk_susar_triggers_hitl_and_electronic_signature(client: TestClient) -> None:
    """Verify SUSAR / Grade 4 toxicity triggers PENDING_HITL_MEDICAL_REVIEW and supports 21 CFR 11 e-signature."""
    payload = {
        "clinical_study_id": "STUDY-IMMUNO-CAR-2026",
        "target_biomarker": "CD19-CAR-T",
        "protocol_text": (
            "Patient: Marcus Vance, MRN: IMM-902114, SSN: 501-33-7741. "
            "Phase I cohort reported a serious SUSAR: Grade 4 cytokine release syndrome "
            "with neurotoxicity and neutropenia requiring clinical hold."
        ),
    }
    res = client.post("/v1/clinical/synthesize", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["consensus_evaluation"]["governance_status"] == "PENDING_HITL_MEDICAL_REVIEW"
    assert body["consensus_evaluation"]["safety_risk_flagged"] is True

    flagged_record_id = body["fda_part11_record"]["record_id"]

    # Append Medical Reviewer HITL Electronic Signature
    sign_payload = {
        "record_id": flagged_record_id,
        "medical_reviewer_id": "MD-ROCHE-4491",
        "electronic_signature_meaning": "Medical Monitor Safety Review & Release Approval (21 CFR 11.50)",
        "approved": True,
        "reviewer_notes": "Confirmed ICU management protocol and DSMB clearance.",
    }
    sign_res = client.post("/v1/hitl/sign-record", json=sign_payload)
    assert sign_res.status_code == 200
    signed_rec = sign_res.json()
    assert signed_rec["record_type"] == "HITL_ELECTRONIC_SIGNATURE"
    assert signed_rec["governance_status"] == "APPROVED_BY_HITL_MEDICAL_REVIEWER"
    assert signed_rec["medical_reviewer_id"] == "MD-ROCHE-4491"
    assert signed_rec["previous_hash"] == body["fda_part11_record"]["current_hash"]


def test_quantum_molecular_screening_and_finops_showback(client: TestClient) -> None:
    """Verify Hybrid Quantum VQE molecular screening and R&D grant FinOps accounting."""
    q_payload = {
        "clinical_study_id": "STUDY-ONCO-KRAS-2026",
        "molecule_smiles": "C=CC(=O)N1CCN(CC1)C2=NC(=O)N(C=C2C3=C(C=CC=C3F)O)C4=C(C=CN=C4C(C)C)C",
        "target_receptor": "KRAS-G12C",
        "num_qubits": 6,
        "ansatz_layers": 3,
    }
    q_res = client.post("/v1/quantum/screen-molecule", json=q_payload)
    assert q_res.status_code == 200
    q_data = q_res.json()

    assert q_data["num_qubits"] == 6
    assert q_data["circuit_depth"] > 0
    assert q_data["cnot_entangling_gates"] == 15
    assert q_data["vqe_ground_state_energy_hartree"] < -70.0
    assert q_data["binding_affinity_kcal_mol"] < -6.0
    assert 0.50 <= q_data["binding_affinity_score"] <= 1.0
    assert len(q_data["convergence_trajectory_hartree"]) >= 6
    assert "[RY(" in q_data["circuit_diagram_ascii"]

    # Check Study FinOps endpoint
    fin_res = client.get("/v1/finops/studies/STUDY-ONCO-KRAS-2026")
    assert fin_res.status_code == 200
    fin_data = fin_res.json()
    assert fin_data["quantum_screening_runs"] == 1
    assert fin_data["total_spent_usd"] > 0.0
    assert "ephemeral_spot_gpu_savings_pct" in fin_data["gpu_infrastructure_comparison"]


def test_finops_hard_budget_cap_enforcement(client: TestClient) -> None:
    """Verify HTTP 402 is returned when a clinical study grant exceeds its allocated R&D budget."""
    tiny_budget_payload = {
        "clinical_study_id": "STUDY-MICRO-GRANT-2026",
        "target_biomarker": "EGFR-L858R",
        "allocated_budget_usd": 0.0005,
        "protocol_text": (
            "Patient: Alice Carter, MRN: ONC-119022. Phase I cohort evaluating EGFR-L858R "
            "inhibitor response with mild rash and Grade 1 diarrhea."
        ),
    }
    res = client.post("/v1/clinical/synthesize", json=tiny_budget_payload)
    assert res.status_code == 402
    assert res.json()["detail"]["error"] == "CLINICAL_STUDY_GRANT_BUDGET_EXCEEDED"


def test_fda_part11_hash_chain_tamper_detection(client: TestClient) -> None:
    """Verify SHA-256 hash chain passes when intact and detects tampering if SQLite row is altered."""
    for idx in range(2):
        res = client.post(
            "/v1/clinical/synthesize",
            json={
                "clinical_study_id": f"STUDY-CHAIN-{idx}",
                "target_biomarker": "KRAS-G12C",
                "protocol_text": (
                    f"Patient: Subject {idx}, MRN: CHN-000{idx}. Protocol evaluation of KRAS-G12C "
                    "cohort with mild nausea and fatigue."
                ),
            },
        )
        assert res.status_code == 200

    ver_ok = client.get("/v1/audit/verify-integrity")
    assert ver_ok.status_code == 200
    assert ver_ok.json()["verified"] is True
    assert ver_ok.json()["total_records_checked"] == 2

    # Simulate unauthorized database tampering on sequence_id = 1
    fda_db_path = os.environ["FDA_LEDGER_DB_PATH"]
    with sqlite3.connect(fda_db_path) as conn:
        conn.execute(
            "UPDATE fda_part11_ledger SET consensus_score = 0.9999 WHERE sequence_id = 1"
        )
        conn.commit()

    ver_tampered = client.get("/v1/audit/verify-integrity")
    assert ver_tampered.status_code == 200
    report = ver_tampered.json()
    assert report["verified"] is False
    assert len(report["tampered_record_ids"]) >= 1


def test_finops_grant_allocation_and_assistant_chat_endpoints(client: TestClient) -> None:
    """Verify interactive FinOps grant allocation and Dual-Persona AI Guide Assistant."""
    alloc_res = client.post(
        "/v1/finops/allocate-grant",
        json={"clinical_study_id": "STUDY-ONCO-KRAS-2026", "allocated_budget_usd": 5000.0},
    )
    assert alloc_res.status_code == 200
    assert alloc_res.json()["allocated_budget_usd"] == 5000.0

    chat_res = client.post(
        "/v1/assistant/chat",
        json={
            "question": "What does it do?",
            "history": [
                {"role": "user", "content": "Tell me about Tab 4 FinOps"},
                {"role": "assistant", "content": "Tab 4 manages clinical study grant budgets."},
            ],
            "persona_mode": "dual",
            "preferred_model": "deterministic-offline",
        },
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert "IN EVERYDAY TERMS" in chat_data["plain_language_summary"]
    assert "FOR THE SCIENTIST" in chat_data["scientific_deep_dive"]
    assert chat_data["turn_count"] == 2
    assert len(chat_data["step_by_step_guide"]) == 4

    q_chat_res = client.post(
        "/v1/assistant/chat",
        json={
            "question": "Explain the Quantum VQE Molecular Screener",
            "persona_mode": "scientist",
            "preferred_model": "deterministic-offline",
        },
    )
    assert q_chat_res.status_code == 200
    assert "Hamiltonian" in q_chat_res.json()["scientific_deep_dive"]



