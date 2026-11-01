# 🧬⚛️ Quantum BioMed Research & GxP Governance Engine

> **Production-Grade Enterprise Reference Platform for Pharmaceutical R&D, GxP Clinical Trial Protocol Synthesis, Pharmacovigilance Multi-Judge Consensus, Hybrid Quantum-AI Molecular Screening (VQE), Clinical Study Token FinOps, and FDA 21 CFR Part 11 Cryptographic Auditability.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-OpenAPI_3.1-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/Frontend-React_18_R%26D_Workbench-61DAFB?style=flat-square&logo=react&logoColor=black)]()
[![Quantum VQE](https://img.shields.io/badge/Quantum_Drug_Discovery-VQE_%28Qiskit_%2B_Statevector%29-6929C4?style=flat-square)]()
[![Compliance](https://img.shields.io/badge/Compliance-FDA_21_CFR_Part_11_%7C_HIPAA_%7C_EU_AI_Act-10B981?style=flat-square)]()
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Helm_Chart_%2B_PVC-326CE5?style=flat-square&logo=kubernetes&logoColor=white)](helm/biomed-gxp-engine)
[![License](https://img.shields.io/badge/License-Apache_2.0-22C55E?style=flat-square)](LICENSE)
[![Maintainer](https://img.shields.io/badge/Maintainer-Marian_Ropota_(LinkedIn)-0A66C2?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/marian-rop)
[![Credly](https://img.shields.io/badge/Certifications-Credly_Verified-FF6B00?style=flat-square&logo=credly)](https://www.credly.com/users/marian-ropota/badges/credly)

---

## 🎯 Executive Value Proposition — For Big Pharma VPs of R&D, Principal Architects & Technical Recruiters

Modern Pharmaceutical R&D and Clinical Trial Operations (**ICH E6(R3) GxP**) face three structural bottlenecks when adopting Generative AI and Quantum Computing:
1. **Unacceptable Regulatory & Patient Safety Risk:** Standard LLMs hallucinate clinical endpoints, omit serious adverse events (**SUSARs**), or leak Protected Health Information (**HIPAA / GDPR PHI**) to external cloud APIs.
2. **Lack of FDA 21 CFR Part 11 Auditability:** Clinical trial systems require tamper-evident electronic records (`§11.10`) and legally binding Human-in-the-Loop (**HITL**) electronic signatures (`§11.50 / §11.70`) from Medical Monitors.
3. **Uncontrolled R&D Compute & Token Spend:** Clinical study grants and in-silico quantum drug discovery campaigns lack per-study chargeback/showback guardrails.

**`quantum-biomed-research-engine`** solves all three in a **100% functional, containerized, full-stack platform (FastAPI Backend + React 18 R&D Workbench + SQLite FDA Part 11 Ledger + Kubernetes Helm Chart)**:

- **🛡️ Deterministic HIPAA / GDPR PHI De-Identification (`src/privacy/phi_scrubber.py`):** Redacts Patient Names, MRNs, SSNs/CNPs, Dates of Birth, Emails, and Phone Numbers *before* any LLM call, recording SHA-256 digests of raw vs. scrubbed payloads.
- **⚖️ 3x Concurrent GxP Multi-Judge Consensus (`src/evaluators/multi_judge_consensus.py`):** Runs `ClinicalGroundednessJudge`, `PharmacovigilanceSafetyJudge`, and `GxPComplianceJudge` concurrently via `asyncio.gather`. Applies a mathematical variance penalty and automatically routes any synthesis with `consensus_score < 0.95` or a high-severity safety signal (`SUSAR`, `Grade 4/5 toxicity`) to **`PENDING_HITL_MEDICAL_REVIEW`**.
- **⚛️ Hybrid Quantum-AI Molecular Screening (`src/agents/quantum_molecular_screener.py`):** Maps candidate ligand **SMILES** strings and disease receptors (`KRAS-G12C`, `EGFR-T790M`, `BACE1`) into a parameterized quantum ansatz (`RY/RZ` rotations + `CNOT` entanglement ladder) to estimate Variational Quantum Eigensolver (**VQE**) ground-state energies ($\text{Ha}$) and binding affinities ($\Delta G$ in $\text{kcal/mol}$).
- **🔗 FDA 21 CFR Part 11 Cryptographic Hash-Chain Ledger (`src/compliance/fda_part11_ledger.py`):** Chains every clinical synthesis, quantum screen, and Medical Reviewer HITL electronic signature using `SHA-256` (`previous_hash` $\to$ `current_hash`) with live mathematical tamper verification (`GET /v1/audit/verify-integrity`).
- **💸 Pharmaceutical & Quantum Grant FinOps (`src/finops/study_budget.py`):** Tracks token and quantum statevector spend strictly per `clinical_study_id` (e.g., `STUDY-ONCO-KRAS-2026`), enforces HTTP `402` hard grant caps, and benchmarks savings against ephemeral Spot GPU NIM infrastructure.
- **🖥️ Modern Biotech SaaS Workbench (`src/static/index.html`):** Features a Left Sidebar + Top Telemetry Bar layout, **Dark Mode / Light Mode Toggle (`☀️ / 🌙`)**, Non-Blocking Background Execution with live stage timers (`⏱️ 0.1s...`), custom SVG Avatar (**Dr. Helix**), and a **Multi-Turn 3-Track Collapsible Copilot** (`+ Extend` preview cards + `🎯 Focus Track` deep-dive continuation).



---

## 🏛️ End-to-End Architecture & Dual-Mode Execution (Standalone + Connected Lab)

Every module in this repository is built with **12-Factor Environment Configuration (`.env`)** and **Dual-Mode Execution**:
- **Mode A — 100% Standalone Out-of-the-Box (`LLM_LIVE_MODE=false` default):** Works immediately after `git clone` with zero API keys or external services. Uses the deterministic GxP clinical synthesizer, 3x concurrent calibration judges, and the built-in pure-Python complex statevector quantum VQE simulator.
- **Mode B — Connected Enterprise Lab (`LLM_LIVE_MODE=true`):** Routes live inference across the [**AI-Governance-Lab**](docs/portfolio-mapping.md) ecosystem:
  - **Tier 1 (`NIM_DIRECT_BASE_URL`):** Direct self-hosted NVIDIA NIM / TensorRT-LLM GPU containers (from `nvidia-nim-enterprise-patterns`).
  - **Tier 2 (`LITELLM_BASE_URL`):** Centralized LiteLLM Gateway (`:4001` from `private-enterprise-ai-hub`) with automatic multi-model failover (`gemini-3.8-flash` $\to$ `glm-5.2` $\to$ `gemini-3.1-pro-preview` $\to$ `nvidia/nemotron-3-ultra-550b-a55b` $\to$ `codestral-2508`).
  - **Tier 3 (Automatic Failover):** Falls back transparently to the deterministic local GxP engine if external gateways are unreachable.

```mermaid
flowchart LR
    A["Raw Clinical Protocol\n(Contains PHI)"] --> B["HIPAA / GDPR\nPHI Scrubber"]
    B --> C["Pharma & Quantum\nStudy Grant FinOps"]
    C --> D["3-Tier Clinical Synthesizer\n[CIT-P1] + AE Extraction"]
    D --> E["3x Concurrent GxP Judges\n(asyncio.gather)"]
    E -->|Score >= 0.95 & Safe| F["APPROVED_AUTONOMOUS"]
    E -->|Score < 0.95 or SUSAR| G["PENDING_HITL_MEDICAL_REVIEW"]
    F --> H["FDA 21 CFR Part 11\nSHA-256 SQLite Ledger"]
    G --> H
    I["SMILES Ligand +\nTarget Receptor"] --> J["Quantum VQE Screener\n(RY/RZ + CNOT Ansatz)"]
    J --> C
    J --> H
    K["Medical Monitor\nHITL E-Signature"] --> H
```

---

## 📋 Regulatory & Compliance Mapping (GxP, FDA 21 CFR Part 11, HIPAA, EU AI Act)

| Regulatory Framework | Requirement | Concrete Implementation in `quantum-biomed-research-engine` |
|---|---|---|
| **FDA 21 CFR Part 11 (§11.10)** | Tamper-evident, time-stamped computer-generated audit trails. | `src/compliance/fda_part11_ledger.py`: Cryptographic SHA-256 hash chaining (`current_hash = sha256(previous_hash + timestamp_utc + study_id + scrubbed_hash + output + score + signature)`), verified via `GET /v1/audit/verify-integrity`. |
| **FDA 21 CFR Part 11 (§11.50 / §11.70)** | Signature manifestations (printed reviewer ID, UTC date/time, meaning) cryptographically linked to their respective electronic records. | `POST /v1/hitl/sign-record`: Appends an immutable `HITL_ELECTRONIC_SIGNATURE` block linking `medical_reviewer_id`, `electronic_signature_meaning`, and the target record's SHA-256 digest. |
| **HIPAA Safe Harbor & GDPR Art. 9** | De-identification of Protected Health Information (PHI) and special-category health data before external processing. | `src/privacy/phi_scrubber.py`: Deterministic regex + rule-based redaction of Patient Names, MRNs, SSNs/CNPs, DOBs, Emails, and Phones prior to any LLM call. |
| **EU AI Act (High-Risk Medical / Annex III)** | Human oversight (Art. 14), accuracy/robustness (Art. 15), and automatic logging (Art. 12). | `src/evaluators/multi_judge_consensus.py`: 3 independent calibration judges with variance penalty and mandatory escalation to `PENDING_HITL_MEDICAL_REVIEW`. |

> **Architectural Scope Note:** This repository is an open-source **enterprise reference architecture** demonstrating GxP, HIPAA, and FDA 21 CFR Part 11 software engineering patterns in code. In a commercial pharmaceutical deployment, production qualification additionally requires formal Computer System Validation (CSV — IQ/OQ/PQ) per GAMP 5.



---

## 🔌 REST API & React 18 Workbench Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | **Interactive React 18 BioMed & Quantum R&D Workbench** (4 tabs: Clinical Synthesis, Quantum VQE Screener, FDA Part 11 Ledger & HITL E-Signature, Pharma/Quantum FinOps). |
| `GET` | `/docs` | Interactive OpenAPI 3.1 / Swagger UI documentation. |
| `GET` | `/healthz` & `/readyz` | Kubernetes liveness and readiness probes (verifies SQLite persistence & SHA-256 ledger integrity). |
| `POST` | `/v1/clinical/synthesize` | Runs HIPAA PHI Scrubber $\to$ FinOps Grant Check $\to$ Clinical Synthesizer (`[CIT-Px]`) $\to$ 3x Concurrent GxP Judges $\to$ FDA Part 11 Ledger. |
| `POST` | `/v1/quantum/screen-molecule` | Runs Hybrid Quantum VQE simulation (`RY/RZ` + `CNOT`) for SMILES drug candidates, charges R&D study budget, and appends to FDA Part 11 Ledger. |
| `POST` | `/v1/hitl/sign-record` | Appends a Medical Reviewer Human-in-the-Loop (HITL) Electronic Signature (`21 CFR §11.50`) linked to a clinical record. |
| `GET` | `/v1/audit/ledger` | Returns historical SHA-256 hash-chained records from the SQLite ledger. |
| `GET` | `/v1/audit/verify-integrity` | Recomputes the entire SHA-256 chain from genesis to mathematically prove zero tampering. |
| `GET` | `/v1/finops/studies/{study_id}` | Returns Clinical Study & Quantum R&D token/compute spend, remaining grant cap, and Spot GPU NIM showback comparison. |

---

## 🚀 Quick Start (Local Python, Docker Compose & Kubernetes Helm)

### 1. Local Python & Automated End-to-End Test Suite (`pytest`)
Works 100% out-of-the-box with zero external API keys required:
```bash
cd quantum-biomed-research-engine
cp .env.example .env

# Run the end-to-end test suite (PHI redaction, 3x GxP judges, Quantum VQE, HITL e-signature, FinOps 402 cap, SHA-256 tamper detection)
pytest -v

# Start the FastAPI backend + React 18 Workbench on http://localhost:8000
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 2. Docker Compose (With Persistent `/data` SQLite FDA Part 11 Volume)
```bash
cp .env.example .env
docker compose up --build -d
# Open http://localhost:8000 for the React 18 Workbench or http://localhost:8000/docs for Swagger UI
```

### 3. Kubernetes / K3s Deployment via Helm Chart
Includes non-root `securityContext` (`uid=10001`), `/healthz` and `/readyz` probes, `ConfigMap`, and `PersistentVolumeClaim` mounted at `/data`:
```bash
helm upgrade --install biomed-gxp-engine ./helm/biomed-gxp-engine \
  --namespace biomed-gxp --create-namespace \
  --set service.nodePort=30089
```
To connect to the centralized **LiteLLM Gateway (`private-enterprise-ai-hub`)** on your LAN cluster:
```bash
helm upgrade --install biomed-gxp-engine ./helm/biomed-gxp-engine \
  --namespace biomed-gxp --create-namespace \
  --set config.LLM_LIVE_MODE="true" \
  --set config.LITELLM_BASE_URL="http://<LITELLM_GATEWAY_IP>:4001/v1"
```

---

## 📚 Ecosystem & Portfolio Documentation

- [**`docs/portfolio-mapping.md`**](docs/portfolio-mapping.md) — How `quantum-biomed-research-engine` integrates with `private-enterprise-ai-hub`, `governed-quantum-agents`, and `nvidia-nim-enterprise-patterns`, plus the **Pharma & Quantum Interview Competency Matrix**.

---

## 👨‍💻 Maintainer & Author

**Marian Ropota** — *Principal AI/ML & Quantum Platform Architect | Regulated Life Sciences AI, Hybrid Cloud Infrastructure & Agentic Engineering*  
🔗 **[LinkedIn](https://www.linkedin.com/in/marian-rop)** • 🏅 **[Credly Certifications](https://www.credly.com/users/marian-ropota/badges/credly)** • 🐙 **[AI Governance Lab](https://github.com/AI-Governance-Lab)**

*Part of the **AI Governance Lab** open-source engineering portfolio — bridging scientific R&D, quantum simulation, and regulated enterprise production.*
