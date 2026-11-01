"""Strict Pydantic v2 Data Models for Pharmaceutical GxP, Quantum R&D & FDA 21 CFR Part 11."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class ClinicalSynthesisRequest(BaseModel):
    """Input payload for clinical trial protocol synthesis and pharmacovigilance audit."""

    model_config = ConfigDict(extra="forbid")

    clinical_study_id: str = Field(
        ...,
        min_length=3,
        max_length=128,
        description="Unique clinical trial or R&D grant identifier (e.g., STUDY-ONCO-KRAS-2026).",
    )
    protocol_text: str = Field(
        ...,
        min_length=20,
        description="Raw clinical trial protocol excerpt, investigator brochure note, or safety narrative.",
    )
    target_biomarker: str = Field(
        ...,
        min_length=2,
        max_length=128,
        description="Target molecular biomarker or receptor under investigation (e.g., KRAS-G12C, EGFR-L858R).",
    )
    allocated_budget_usd: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Optional custom R&D grant cap in USD for this clinical study.",
    )
    preferred_model: Optional[str] = Field(
        default=None,
        description="Optional model override for LiteLLM / NVIDIA NIM gateway routing.",
    )


class ScrubbedPayload(BaseModel):
    """Output of deterministic HIPAA / GDPR Protected Health Information (PHI) scrubber."""

    model_config = ConfigDict(extra="forbid")

    scrubbed_text: str
    original_sha256: str
    scrubbed_sha256: str
    total_redactions: int = Field(..., ge=0)
    redaction_breakdown: Dict[str, int] = Field(default_factory=dict)
    hipaa_safe_harbor_compliant: bool = True


class JudgeScore(BaseModel):
    """Individual evaluation output from an independent GxP calibration judge."""

    model_config = ConfigDict(extra="forbid")

    judge_name: str
    score: float = Field(..., ge=0.0, le=1.0)
    weight: float = Field(..., gt=0.0, le=1.0)
    passed: bool
    flagged_risk: bool = False
    findings: List[str] = Field(default_factory=list)


class ConsensusEvaluationResult(BaseModel):
    """Aggregated multi-judge consensus result with mathematical variance penalty."""

    model_config = ConfigDict(extra="forbid")

    weighted_mean_score: float = Field(..., ge=0.0, le=1.0)
    score_variance: float = Field(..., ge=0.0)
    variance_penalty: float = Field(..., ge=0.0)
    consensus_score: float = Field(..., ge=0.0, le=1.0)
    threshold_required: float = Field(..., ge=0.0, le=1.0)
    safety_risk_flagged: bool
    governance_status: Literal["APPROVED_AUTONOMOUS", "PENDING_HITL_MEDICAL_REVIEW"]
    judges: List[JudgeScore] = Field(default_factory=list)


class ClinicalSynthesisOutput(BaseModel):
    """Structured clinical protocol synthesis and pharmacovigilance extraction."""

    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    clinical_study_id: str
    target_biomarker: str
    executive_clinical_synthesis: str
    paragraph_citations: List[str]
    extracted_adverse_events: List[str]
    contraindications_and_warnings: List[str]
    execution_tier: str
    model_used: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class FDAPart11AuditRecord(BaseModel):
    """Immutable FDA 21 CFR Part 11 record with SHA-256 cryptographic hash chaining."""

    model_config = ConfigDict(extra="forbid")

    record_id: str
    sequence_id: int
    timestamp_utc: str
    clinical_study_id: str
    record_type: Literal["CLINICAL_SYNTHESIS", "QUANTUM_SCREENING", "HITL_ELECTRONIC_SIGNATURE"]
    target_biomarker_or_receptor: str
    scrubbed_prompt_hash: str
    synthesis_output: str
    consensus_score: float
    governance_status: str
    medical_reviewer_id: Optional[str] = None
    electronic_signature_meaning: Optional[str] = None
    reviewer_signature_hash: str
    previous_hash: str
    current_hash: str


class ClinicalSynthesisResponse(BaseModel):
    """Complete end-to-end response from POST /v1/clinical/synthesize."""

    model_config = ConfigDict(extra="forbid")

    clinical_study_id: str
    target_biomarker: str
    privacy_audit: ScrubbedPayload
    synthesis: ClinicalSynthesisOutput
    consensus_evaluation: ConsensusEvaluationResult
    finops_tx_cost_usd: float
    remaining_study_budget_usd: float
    fda_part11_record: FDAPart11AuditRecord


class QuantumScreeningRequest(BaseModel):
    """Input payload for Hybrid Quantum-AI molecular binding & VQE screening."""

    model_config = ConfigDict(extra="forbid")

    clinical_study_id: str = Field(
        default="STUDY-ONCO-KRAS-2026",
        min_length=3,
        max_length=128,
        description="Clinical study grant under which the in-silico screening is billed and audited.",
    )
    molecule_smiles: str = Field(
        ...,
        min_length=2,
        max_length=512,
        description="Canonical SMILES string of the candidate ligand/drug molecule.",
    )
    target_receptor: str = Field(
        ...,
        min_length=2,
        max_length=128,
        description="Target protein receptor or binding pocket (e.g., KRAS-G12C, EGFR-T790M, BACE1).",
    )
    num_qubits: int = Field(
        default=6,
        ge=2,
        le=12,
        description="Number of active-space molecular orbitals mapped to qubits (2 to 12).",
    )
    ansatz_layers: int = Field(
        default=3,
        ge=1,
        le=8,
        description="Number of RY/RZ + CNOT entanglement variational layers.",
    )


class QuantumScreeningResponse(BaseModel):
    """Output of hybrid quantum VQE molecular screening with telemetry and ledger receipt."""

    model_config = ConfigDict(extra="forbid")

    clinical_study_id: str
    molecule_smiles: str
    target_receptor: str
    num_qubits: int
    ansatz_layers: int
    circuit_depth: int
    cnot_entangling_gates: int
    single_qubit_rotation_gates: int
    quantum_backend_used: str
    vqe_ground_state_energy_hartree: float
    binding_affinity_kcal_mol: float
    binding_affinity_score: float
    convergence_trajectory_hartree: List[float]
    dominant_bitstring: str
    dominant_state_probability: float
    circuit_diagram_ascii: str
    drug_likeness_verdict: str
    finops_screening_cost_usd: float
    remaining_study_budget_usd: float
    fda_part11_record: FDAPart11AuditRecord


class HITLApprovalRequest(BaseModel):
    """FDA 21 CFR Part 11 §11.50 / §11.70 Human-in-the-Loop Electronic Signature request."""

    model_config = ConfigDict(extra="forbid")

    record_id: str = Field(..., min_length=4, description="Target FDA Part 11 record_id to sign/adjudicate.")
    medical_reviewer_id: str = Field(
        ...,
        min_length=3,
        max_length=128,
        description="Authenticated Medical Monitor / Principal Investigator ID (e.g., MD-ROCHE-4491).",
    )
    electronic_signature_meaning: str = Field(
        ...,
        min_length=5,
        max_length=256,
        description="Regulatory meaning of signature per 21 CFR §11.50.",
    )
    approved: bool = Field(
        ...,
        description="True to approve the clinical record for release; False to reject/quarantine.",
    )
    reviewer_notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional clinical addendum recorded in the immutable ledger.",
    )


class LedgerIntegrityReport(BaseModel):
    """Cryptographic verification report for the entire FDA 21 CFR Part 11 hash chain."""

    model_config = ConfigDict(extra="forbid")

    verified: bool
    total_records_checked: int
    genesis_hash: str
    latest_hash: str
    tampered_record_ids: List[str] = Field(default_factory=list)
    verification_timestamp_utc: str
    regulatory_standard: str = "FDA 21 CFR Part 11 (§11.10 / §11.50 / §11.70) & EU AI Act Annex III"


class StudyFinOpsReport(BaseModel):
    """Pharmaceutical & Quantum R&D Clinical Study Grant Chargeback/Showback report."""

    model_config = ConfigDict(extra="forbid")

    clinical_study_id: str
    allocated_budget_usd: float
    total_spent_usd: float
    remaining_budget_usd: float
    budget_utilization_pct: float
    clinical_synthesis_runs: int
    quantum_screening_runs: int
    total_prompt_tokens: int
    total_completion_tokens: int
    clinical_ai_spend_usd: float
    quantum_vqe_spend_usd: float
    avg_cost_per_clinical_synthesis_usd: float
    avg_cost_per_screened_molecule_usd: float
    budget_status: Literal["HEALTHY", "WARNING_NEAR_CAP", "EXHAUSTED_HARD_CAP"]
    gpu_infrastructure_comparison: Dict[str, Any]


class FinOpsGrantAllocationRequest(BaseModel):
    """Request to allocate, top-up, or adjust a Clinical Study & Quantum R&D Grant budget cap."""

    model_config = ConfigDict(extra="forbid")

    clinical_study_id: str = Field(
        ...,
        min_length=3,
        max_length=128,
        description="Clinical study grant identifier (e.g., STUDY-ONCO-KRAS-2026).",
    )
    allocated_budget_usd: float = Field(
        ...,
        gt=0.0,
        le=10000000.0,
        description="New total allocated USD budget cap for this study grant.",
    )


class ChatTurn(BaseModel):
    """Single conversational turn in the multi-turn BioMed & Quantum R&D chat."""

    model_config = ConfigDict(extra="ignore")

    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=12000)


class AssistantChatRequest(BaseModel):
    """Input payload for the Dual-Persona BioMed & Quantum R&D Guide Assistant."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(..., min_length=2, max_length=4000)
    history: List[ChatTurn] = Field(
        default_factory=list,
        description="Prior multi-turn conversation history between user and Dr. Helix assistant.",
    )
    persona_mode: Literal["dual", "plain", "scientist", "steps"] = Field(
        default="dual",
        description="Explanation track: 'plain', 'scientist', 'steps', or 'dual' (all 3 tracks).",
    )
    preferred_model: Optional[str] = Field(default=None)
    active_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional live telemetry snapshot from the UI (latest clinical/quantum/finops state).",
    )


class AssistantChatResponse(BaseModel):
    """Structured response from the BioMed & Quantum R&D Guide Assistant."""

    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    question: str
    persona_mode: str
    plain_language_summary: str
    scientific_deep_dive: str
    step_by_step_guide: List[str]
    suggested_followups: List[str]
    execution_tier: str
    model_used: str
    turn_count: int = 1



