"""12-Factor Environment Configuration for the Quantum BioMed Research Engine."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from dotenv import load_dotenv

load_dotenv()


def _b(key: str, default: bool = False) -> bool:
    val = os.getenv(key)
    return default if val is None else val.strip().lower() in {"1", "true", "yes", "on"}


def _f(key: str, default: float) -> float:
    return float(os.getenv(key, str(default)))


def _i(key: str, default: int) -> int:
    return int(os.getenv(key, str(default)))


def _s(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


def _csv(key: str, default: List[str]) -> List[str]:
    val = os.getenv(key)
    if not val:
        return list(default)
    items = [x.strip() for x in val.split(",") if x.strip()]
    return items if items else list(default)


@dataclass(frozen=True)
class EngineSettings:
    """Immutable runtime settings populated from environment variables."""

    app_name: str
    app_version: str
    app_env: str
    api_bind_host: str
    api_bind_port: int
    log_level: str

    data_dir: str
    fda_ledger_db_path: str
    finops_budget_db_path: str

    llm_live_mode: bool
    nim_direct_base_url: str
    nim_direct_api_key: str
    nim_direct_model: str
    litellm_base_url: str
    litellm_api_key: str
    litellm_primary_model: str
    litellm_fallback_models: List[str] = field(default_factory=list)
    litellm_timeout_seconds: float = 30.0
    litellm_temperature: float = 0.15

    gxp_consensus_threshold: float = 0.95
    judge_weight_groundedness: float = 0.40
    judge_weight_pharmacovigilance: float = 0.40
    judge_weight_gxp_compliance: float = 0.20
    judge_variance_penalty_factor: float = 0.50

    default_study_grant_budget_usd: float = 2500.00
    synthesis_cost_per_1k_tokens_usd: float = 0.0045
    multi_judge_cost_per_1k_tokens_usd: float = 0.0060
    quantum_screen_base_cost_usd: float = 0.1200
    quantum_cost_per_qubit_depth_usd: float = 0.0025
    nim_l4_spot_hourly_usd: float = 0.28
    nim_l4_ondemand_hourly_usd: float = 0.95
    cloud_proprietary_api_equivalent_multiplier: float = 3.40

    quantum_backend_preference: str = "auto"
    quantum_default_qubits: int = 6
    quantum_max_qubits: int = 12
    quantum_default_ansatz_layers: int = 3
    quantum_vqe_iterations: int = 12

    k8s_nodeport: int = 30089
    sibling_gqa_workbench_url: str = "http://localhost:30088"
    sibling_private_hub_url: str = "http://localhost:8080"


def get_settings() -> EngineSettings:
    """Load current settings from environment variables and ensure data directories exist."""
    data_dir = _s("DATA_DIR", "./data")
    fda_db = _s("FDA_LEDGER_DB_PATH", os.path.join(data_dir, "fda_part11_audit_ledger.db"))
    finops_db = _s("FINOPS_BUDGET_DB_PATH", os.path.join(data_dir, "clinical_study_finops.db"))

    for db_file in (fda_db, finops_db):
        Path(db_file).parent.mkdir(parents=True, exist_ok=True)

    return EngineSettings(
        app_name=_s("APP_NAME", "Quantum BioMed R&D Governance Engine"),
        app_version=_s("APP_VERSION", "1.0.0"),
        app_env=_s("APP_ENV", "production"),
        api_bind_host=_s("API_BIND_HOST", "0.0.0.0"),
        api_bind_port=_i("API_BIND_PORT", 8000),
        log_level=_s("LOG_LEVEL", "INFO"),
        data_dir=data_dir,
        fda_ledger_db_path=fda_db,
        finops_budget_db_path=finops_db,
        llm_live_mode=_b("LLM_LIVE_MODE", False),
        nim_direct_base_url=_s("NIM_DIRECT_BASE_URL", "").rstrip("/"),
        nim_direct_api_key=_s("NIM_DIRECT_API_KEY", ""),
        nim_direct_model=_s("NIM_DIRECT_MODEL", "deepseek-ai/deepseek-r1-distill-llama-8b"),
        litellm_base_url=_s("LITELLM_BASE_URL", "http://localhost:4001/v1").rstrip("/"),
        litellm_api_key=_s("LITELLM_API_KEY", ""),
        litellm_primary_model=_s("LITELLM_PRIMARY_MODEL", "gemini-3.8-flash"),
        litellm_fallback_models=_csv(
            "LITELLM_FALLBACK_MODELS",
            ["glm-5.2", "gemini-3.1-pro-preview", "nvidia/nemotron-3-ultra-550b-a55b", "codestral-2508"],
        ),
        litellm_timeout_seconds=_f("LITELLM_TIMEOUT_SECONDS", 30.0),
        litellm_temperature=_f("LITELLM_TEMPERATURE", 0.15),
        gxp_consensus_threshold=_f("GXP_CONSENSUS_THRESHOLD", 0.95),
        judge_weight_groundedness=_f("JUDGE_WEIGHT_GROUNDEDNESS", 0.40),
        judge_weight_pharmacovigilance=_f("JUDGE_WEIGHT_PHARMACOVIGILANCE", 0.40),
        judge_weight_gxp_compliance=_f("JUDGE_WEIGHT_GXP_COMPLIANCE", 0.20),
        judge_variance_penalty_factor=_f("JUDGE_VARIANCE_PENALTY_FACTOR", 0.50),
        default_study_grant_budget_usd=_f("DEFAULT_STUDY_GRANT_BUDGET_USD", 2500.00),
        synthesis_cost_per_1k_tokens_usd=_f("SYNTHESIS_COST_PER_1K_TOKENS_USD", 0.0045),
        multi_judge_cost_per_1k_tokens_usd=_f("MULTI_JUDGE_COST_PER_1K_TOKENS_USD", 0.0060),
        quantum_screen_base_cost_usd=_f("QUANTUM_SCREEN_BASE_COST_USD", 0.1200),
        quantum_cost_per_qubit_depth_usd=_f("QUANTUM_COST_PER_QUBIT_DEPTH_USD", 0.0025),
        nim_l4_spot_hourly_usd=_f("NIM_L4_SPOT_HOURLY_USD", 0.28),
        nim_l4_ondemand_hourly_usd=_f("NIM_L4_ONDEMAND_HOURLY_USD", 0.95),
        cloud_proprietary_api_equivalent_multiplier=_f("CLOUD_PROPRIETARY_API_EQUIVALENT_MULTIPLIER", 3.40),
        quantum_backend_preference=_s("QUANTUM_BACKEND_PREFERENCE", "auto").lower(),
        quantum_default_qubits=_i("QUANTUM_DEFAULT_QUBITS", 6),
        quantum_max_qubits=_i("QUANTUM_MAX_QUBITS", 12),
        quantum_default_ansatz_layers=_i("QUANTUM_DEFAULT_ANSATZ_LAYERS", 3),
        quantum_vqe_iterations=_i("QUANTUM_VQE_ITERATIONS", 12),
        k8s_nodeport=_i("K8S_NODEPORT", 30089),
        sibling_gqa_workbench_url=_s("SIBLING_GQA_WORKBENCH_URL", "http://localhost:30088"),
        sibling_private_hub_url=_s("SIBLING_PRIVATE_HUB_URL", "http://localhost:8080"),
    )
