"""FastAPI Production Service for Quantum BioMed Research Engine.

Exposes:
- GET  /                              -> Interactive React 18 BioMed & Quantum R&D Workbench
- GET  /healthz                       -> Kubernetes liveness probe
- GET  /readyz                        -> Kubernetes readiness probe (verifies SQLite + hash-chain)
- GET  /v1/config/runtime             -> Non-secret 12-Factor runtime & 3-tier routing telemetry
- POST /v1/clinical/synthesize        -> PHI Scrubber -> FinOps Check -> Synthesis -> 3x Multi-Judge -> FDA Part 11 Ledger
- POST /v1/quantum/screen-molecule    -> Hybrid Quantum VQE Screening -> FinOps Check -> FDA Part 11 Ledger
- POST /v1/hitl/sign-record           -> FDA 21 CFR Part 11 Human-in-the-Loop Electronic Signature
- GET  /v1/audit/ledger               -> Historical SHA-256 hash-chained records
- GET  /v1/audit/verify-integrity     -> Mathematical proof of zero ledger tampering
- GET  /v1/finops/studies             -> List all R&D study grants & showback analytics
- GET  /v1/finops/studies/{study_id}  -> Detailed R&D grant spend, remaining budget & GPU NIM comparison
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from src.agents.assistant_guide import BioMedAssistantGuide
from src.agents.clinical_synthesizer import ClinicalTrialSynthesizer
from src.agents.quantum_molecular_screener import QISKIT_AVAILABLE, QuantumMolecularScreener
from src.compliance.fda_part11_ledger import FDAPart11Ledger
from src.config import get_settings
from src.evaluators.multi_judge_consensus import CalibratedMultiJudgeConsensus
from src.finops.study_budget import ClinicalStudyBudgetController, StudyBudgetExceededError
from src.privacy.phi_scrubber import PHIScrubber
from src.schemas import (
    AssistantChatRequest,
    AssistantChatResponse,
    ClinicalSynthesisRequest,
    ClinicalSynthesisResponse,
    FDAPart11AuditRecord,
    FinOpsGrantAllocationRequest,
    HITLApprovalRequest,
    LedgerIntegrityReport,
    QuantumScreeningRequest,
    QuantumScreeningResponse,
    StudyFinOpsReport,
)

settings_boot = get_settings()

app = FastAPI(
    title=settings_boot.app_name,
    version=settings_boot.app_version,
    description=(
        "Enterprise Pharmaceutical R&D, Clinical Trial Protocol Synthesis (GxP), "
        "Pharmacovigilance Multi-Judge Consensus, Hybrid Quantum-AI Molecular Screening (VQE), "
        "Clinical Study Grant FinOps, and FDA 21 CFR Part 11 Cryptographic Audit Engine."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_workbench_ui() -> Any:
    """Serve the interactive React 18 Pharma & Quantum R&D Workbench."""
    static_index = Path(__file__).resolve().parent / "static" / "index.html"
    if static_index.exists():
        return FileResponse(
            str(static_index),
            media_type="text/html",
            headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0", "Pragma": "no-cache"},
        )
    return HTMLResponse(
        "<h1>Quantum BioMed R&D Governance Engine is running.</h1>"
        "<p>Open <a href='/docs'>/docs</a> for OpenAPI specification.</p>"
    )


@app.get("/healthz", tags=["Kubernetes Probes"])
async def healthz() -> Dict[str, Any]:
    """Kubernetes liveness probe."""
    cfg = get_settings()
    return {
        "status": "ok",
        "service": cfg.app_name,
        "version": cfg.app_version,
        "environment": cfg.app_env,
        "llm_live_mode": cfg.llm_live_mode,
        "qiskit_accelerated": QISKIT_AVAILABLE,
    }


@app.get("/readyz", tags=["Kubernetes Probes"])
async def readyz() -> Dict[str, Any]:
    """Kubernetes readiness probe validating SQLite persistence and ledger integrity."""
    cfg = get_settings()
    ledger = FDAPart11Ledger(settings=cfg)
    finops = ClinicalStudyBudgetController(settings=cfg)
    integrity = ledger.verify_ledger_integrity()
    finops.ensure_study_exists("STUDY-ONCO-KRAS-2026")
    if not integrity.verified:
        raise HTTPException(
            status_code=503,
            detail=f"FDA Part 11 Ledger integrity check failed: {integrity.tampered_record_ids}",
        )
    return {
        "status": "ready",
        "ledger_verified": integrity.verified,
        "total_audit_records": integrity.total_records_checked,
        "fda_ledger_db_path": cfg.fda_ledger_db_path,
        "finops_budget_db_path": cfg.finops_budget_db_path,
    }


@app.get("/v1/config/runtime", tags=["System & Portfolio Telemetry"])
async def get_runtime_config() -> Dict[str, Any]:
    """Return non-secret 12-Factor runtime settings and sibling portfolio links."""
    cfg = get_settings()
    return {
        "app_name": cfg.app_name,
        "app_version": cfg.app_version,
        "llm_live_mode": cfg.llm_live_mode,
        "tier_1_nim_direct_configured": bool(cfg.nim_direct_base_url),
        "tier_2_litellm_gateway_url": cfg.litellm_base_url,
        "litellm_primary_model": cfg.litellm_primary_model,
        "litellm_fallback_models": cfg.litellm_fallback_models,
        "gxp_consensus_threshold": cfg.gxp_consensus_threshold,
        "default_study_grant_budget_usd": cfg.default_study_grant_budget_usd,
        "quantum_backend": "qiskit" if QISKIT_AVAILABLE else "pure_python_complex_statevector",
        "k8s_nodeport": cfg.k8s_nodeport,
        "sibling_gqa_workbench_url": cfg.sibling_gqa_workbench_url,
        "sibling_private_hub_url": cfg.sibling_private_hub_url,
    }


@app.get("/v1/models", tags=["System & Portfolio Telemetry"])
async def list_available_models() -> Dict[str, Any]:
    """Return available LLM models from LiteLLM gateway and deterministic fallback."""
    cfg = get_settings()
    models = [
        {
            "id": "",
            "label": f"Auto Gateway ({cfg.litellm_primary_model} + Multi-Model Failover)",
            "provider": "LiteLLM Gateway (:4001)",
        },
        {
            "id": "gemini-3.8-flash",
            "label": "Google Gemini 3.8 Flash (Vertex AI • Fast Clinical Synthesis)",
            "provider": "Google Cloud Vertex AI",
        },
        {
            "id": "glm-5.2",
            "label": "Zhipu GLM-5.2 MaaS (Vertex AI • 1M Context Protocol Reasoning)",
            "provider": "Google Cloud Vertex AI MaaS",
        },
        {
            "id": "gemini-3.1-pro-preview",
            "label": "Google Gemini 3.1 Pro Preview (Vertex AI • Deep GxP Reasoning)",
            "provider": "Google Cloud Vertex AI",
        },
        {
            "id": "gemini-4-argon",
            "label": "Google Gemini 4 Argon (Vertex AI • Scientific Synthesis)",
            "provider": "Google Cloud Vertex AI",
        },
        {
            "id": "codestral-2508",
            "label": "Mistral Codestral 2508 (256k Context)",
            "provider": "Mistral AI",
        },
        {
            "id": "ministral-14b-latest",
            "label": "Mistral Ministral 14B (General Clinical Instructions)",
            "provider": "Mistral AI",
        },
        {
            "id": "nvidia/nemotron-3-ultra-550b-a55b",
            "label": "NVIDIA Nemotron 3 Ultra 550B (NVIDIA NIM Frontier MoE)",
            "provider": "NVIDIA NIM",
        },
        {
            "id": "deepseek-ai/deepseek-v4-flash-0731",
            "label": "DeepSeek v4 Flash (NVIDIA NIM High-Speed Reasoning)",
            "provider": "NVIDIA NIM",
        },
        {
            "id": "deterministic-offline",
            "label": "Deterministic Local GxP Engine (Zero-Token Offline Fallback)",
            "provider": "Local Built-In Engine",
        },
    ]
    return {"default_model": cfg.litellm_primary_model, "llm_live_mode": cfg.llm_live_mode, "models": models}



@app.post(
    "/v1/clinical/synthesize",
    response_model=ClinicalSynthesisResponse,
    tags=["Clinical Trial Synthesis & GxP Multi-Judge"],
)
async def synthesize_clinical_protocol(req: ClinicalSynthesisRequest) -> ClinicalSynthesisResponse:
    """Execute PHI Scrubbing -> FinOps Grant Check -> Clinical Synthesis -> 3x Multi-Judge -> FDA Part 11 Ledger."""
    cfg = get_settings()
    scrubber = PHIScrubber()
    finops = ClinicalStudyBudgetController(settings=cfg)
    synthesizer = ClinicalTrialSynthesizer(settings=cfg)
    consensus_engine = CalibratedMultiJudgeConsensus(settings=cfg)
    ledger = FDAPart11Ledger(settings=cfg)

    privacy_audit = scrubber.scrub(req.protocol_text)

    estimated_prompt_tok = max(24, len(privacy_audit.scrubbed_text.split()) * 2)
    finops.ensure_study_exists(req.clinical_study_id, req.allocated_budget_usd)
    prelim_report = finops.get_study_report(req.clinical_study_id)
    min_estimated_cost = finops.estimate_clinical_synthesis_cost(estimated_prompt_tok, 64)
    if min_estimated_cost > prelim_report.remaining_budget_usd + 1e-9:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "CLINICAL_STUDY_GRANT_BUDGET_EXCEEDED",
                "clinical_study_id": req.clinical_study_id,
                "required_usd": min_estimated_cost,
                "remaining_budget_usd": prelim_report.remaining_budget_usd,
            },
        )

    synthesis = await synthesizer.synthesize(
        clinical_study_id=req.clinical_study_id,
        target_biomarker=req.target_biomarker,
        scrubbed_text=privacy_audit.scrubbed_text,
        preferred_model=req.preferred_model,
    )

    try:
        tx_cost_usd, remaining_usd = finops.check_and_charge_clinical(
            clinical_study_id=req.clinical_study_id,
            prompt_tokens=synthesis.prompt_tokens,
            completion_tokens=synthesis.completion_tokens,
            allocated_budget_usd=req.allocated_budget_usd,
        )
    except StudyBudgetExceededError as exc:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "CLINICAL_STUDY_GRANT_BUDGET_EXCEEDED",
                "clinical_study_id": exc.clinical_study_id,
                "required_usd": exc.requested_usd,
                "remaining_budget_usd": exc.remaining_usd,
            },
        ) from exc

    historical_analytics = ledger.get_governance_analytics()
    consensus = await consensus_engine.evaluate(
        scrubbed_source=privacy_audit.scrubbed_text,
        synthesis=synthesis,
        historical_analytics=historical_analytics,
    )

    fda_record = ledger.append_record(
        clinical_study_id=req.clinical_study_id,
        record_type="CLINICAL_SYNTHESIS",
        target_biomarker_or_receptor=req.target_biomarker,
        scrubbed_prompt_hash=privacy_audit.scrubbed_sha256,
        synthesis_output=synthesis.executive_clinical_synthesis,
        consensus_score=consensus.consensus_score,
        governance_status=consensus.governance_status,
    )

    return ClinicalSynthesisResponse(
        clinical_study_id=req.clinical_study_id,
        target_biomarker=req.target_biomarker,
        privacy_audit=privacy_audit,
        synthesis=synthesis,
        consensus_evaluation=consensus,
        finops_tx_cost_usd=tx_cost_usd,
        remaining_study_budget_usd=remaining_usd,
        fda_part11_record=fda_record,
    )



@app.post(
    "/v1/quantum/screen-molecule",
    response_model=QuantumScreeningResponse,
    tags=["Hybrid Quantum-AI Drug Discovery"],
)
async def screen_molecule_quantum(req: QuantumScreeningRequest) -> QuantumScreeningResponse:
    """Execute Hybrid Quantum VQE molecular screening and record in FDA Part 11 Ledger."""
    cfg = get_settings()
    screener = QuantumMolecularScreener(settings=cfg)
    finops = ClinicalStudyBudgetController(settings=cfg)
    ledger = FDAPart11Ledger(settings=cfg)

    sim_out = screener.screen_molecule(
        molecule_smiles=req.molecule_smiles,
        target_receptor=req.target_receptor,
        num_qubits=req.num_qubits,
        ansatz_layers=req.ansatz_layers,
    )

    try:
        tx_cost_usd, remaining_usd = finops.check_and_charge_quantum(
            clinical_study_id=req.clinical_study_id,
            num_qubits=sim_out["num_qubits"],
            circuit_depth=sim_out["circuit_depth"],
        )
    except StudyBudgetExceededError as exc:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "CLINICAL_STUDY_GRANT_BUDGET_EXCEEDED",
                "clinical_study_id": exc.clinical_study_id,
                "required_usd": exc.requested_usd,
                "remaining_budget_usd": exc.remaining_usd,
            },
        ) from exc

    smiles_hash = hashlib.sha256(
        f"{req.molecule_smiles}|{req.target_receptor}|{req.num_qubits}".encode("utf-8")
    ).hexdigest()
    summary_str = (
        f"VQE Ground Energy={sim_out['vqe_ground_state_energy_hartree']} Ha | "
        f"Binding Affinity={sim_out['binding_affinity_kcal_mol']} kcal/mol | "
        f"Score={sim_out['binding_affinity_score']} | Verdict={sim_out['drug_likeness_verdict']}"
    )

    fda_record = ledger.append_record(
        clinical_study_id=req.clinical_study_id,
        record_type="QUANTUM_SCREENING",
        target_biomarker_or_receptor=req.target_receptor,
        scrubbed_prompt_hash=smiles_hash,
        synthesis_output=summary_str,
        consensus_score=sim_out["binding_affinity_score"],
        governance_status="QUANTUM_IN_SILICO_VERIFIED",
    )

    return QuantumScreeningResponse(
        clinical_study_id=req.clinical_study_id,
        molecule_smiles=req.molecule_smiles,
        target_receptor=req.target_receptor,
        num_qubits=sim_out["num_qubits"],
        ansatz_layers=sim_out["ansatz_layers"],
        circuit_depth=sim_out["circuit_depth"],
        cnot_entangling_gates=sim_out["cnot_entangling_gates"],
        single_qubit_rotation_gates=sim_out["single_qubit_rotation_gates"],
        quantum_backend_used=sim_out["quantum_backend_used"],
        vqe_ground_state_energy_hartree=sim_out["vqe_ground_state_energy_hartree"],
        binding_affinity_kcal_mol=sim_out["binding_affinity_kcal_mol"],
        binding_affinity_score=sim_out["binding_affinity_score"],
        convergence_trajectory_hartree=sim_out["convergence_trajectory_hartree"],
        dominant_bitstring=sim_out["dominant_bitstring"],
        dominant_state_probability=sim_out["dominant_state_probability"],
        circuit_diagram_ascii=sim_out["circuit_diagram_ascii"],
        drug_likeness_verdict=sim_out["drug_likeness_verdict"],
        finops_screening_cost_usd=tx_cost_usd,
        remaining_study_budget_usd=remaining_usd,
        fda_part11_record=fda_record,
    )




@app.post(
    "/v1/hitl/sign-record",
    response_model=FDAPart11AuditRecord,
    tags=["FDA 21 CFR Part 11 Ledger & HITL Electronic Signatures"],
)
async def sign_clinical_record_hitl(req: HITLApprovalRequest) -> FDAPart11AuditRecord:
    """Append an FDA 21 CFR Part 11 Electronic Signature from a Medical Reviewer."""
    cfg = get_settings()
    ledger = FDAPart11Ledger(settings=cfg)
    try:
        return ledger.sign_record_hitl(req)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get(
    "/v1/audit/ledger",
    response_model=List[FDAPart11AuditRecord],
    tags=["FDA 21 CFR Part 11 Ledger & HITL Electronic Signatures"],
)
async def get_audit_ledger(limit: int = Query(default=50, ge=1, le=500)) -> List[FDAPart11AuditRecord]:
    """Return historical FDA Part 11 cryptographic audit records."""
    cfg = get_settings()
    ledger = FDAPart11Ledger(settings=cfg)
    return ledger.list_records(limit=limit)


@app.get(
    "/v1/audit/verify-integrity",
    response_model=LedgerIntegrityReport,
    tags=["FDA 21 CFR Part 11 Ledger & HITL Electronic Signatures"],
)
async def verify_audit_ledger_integrity() -> LedgerIntegrityReport:
    """Mathematically verify the entire SHA-256 hash chain from genesis to latest record."""
    cfg = get_settings()
    ledger = FDAPart11Ledger(settings=cfg)
    return ledger.verify_ledger_integrity()


@app.get(
    "/v1/audit/analytics",
    tags=["FDA 21 CFR Part 11 Ledger & HITL Electronic Signatures"],
)
async def get_audit_governance_analytics() -> Dict[str, Any]:
    """Return overall average consensus score, grouped averages (study/type/biomarker), and history."""
    cfg = get_settings()
    ledger = FDAPart11Ledger(settings=cfg)
    return ledger.get_governance_analytics()


@app.get(
    "/v1/finops/studies",
    response_model=List[StudyFinOpsReport],
    tags=["Pharmaceutical & Quantum R&D Grant FinOps"],
)
async def list_clinical_study_budgets() -> List[StudyFinOpsReport]:
    """List Chargeback/Showback FinOps metrics across all clinical trial & quantum grants."""
    cfg = get_settings()
    finops = ClinicalStudyBudgetController(settings=cfg)
    studies = finops.list_studies()
    if not studies:
        return [finops.get_study_report("STUDY-ONCO-KRAS-2026")]
    return studies


@app.get(
    "/v1/finops/studies/{clinical_study_id}",
    response_model=StudyFinOpsReport,
    tags=["Pharmaceutical & Quantum R&D Grant FinOps"],
)
async def get_clinical_study_budget(clinical_study_id: str) -> StudyFinOpsReport:
    """Return R&D token spend, remaining grant budget, and GPU NIM comparison for a clinical study."""
    cfg = get_settings()
    finops = ClinicalStudyBudgetController(settings=cfg)
    return finops.get_study_report(clinical_study_id)


@app.post(
    "/v1/finops/allocate-grant",
    response_model=StudyFinOpsReport,
    tags=["Pharmaceutical & Quantum R&D Grant FinOps"],
)
async def allocate_or_update_study_grant(req: FinOpsGrantAllocationRequest) -> StudyFinOpsReport:
    """Allocate a new clinical study grant or update the USD budget cap of an existing study."""
    cfg = get_settings()
    finops = ClinicalStudyBudgetController(settings=cfg)
    finops.ensure_study_exists(req.clinical_study_id, req.allocated_budget_usd)
    return finops.get_study_report(req.clinical_study_id)


@app.post(
    "/v1/assistant/chat",
    response_model=AssistantChatResponse,
    tags=["AI Guide & Scientific Assistant"],
)
async def chat_with_biomed_assistant(req: AssistantChatRequest) -> AssistantChatResponse:
    """Explain the platform and live results in everyday plain language and scientific depth."""
    cfg = get_settings()
    assistant = BioMedAssistantGuide(settings=cfg)
    return await assistant.answer_question(req)



if __name__ == "__main__":
    import uvicorn

    runtime_cfg = get_settings()
    uvicorn.run(
        "src.main:app",
        host=runtime_cfg.api_bind_host,
        port=int(os.getenv("API_BIND_PORT", str(runtime_cfg.api_bind_port))),
        reload=False,
    )

