"""Dual-Persona BioMed, Quantum VQE & GxP Governance AI Assistant Guide."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from src.config import EngineSettings, get_settings
from src.schemas import AssistantChatRequest, AssistantChatResponse

logger = logging.getLogger(__name__)


class BioMedAssistantGuide:
    """Dual-mode interactive assistant for the Quantum BioMed Research Engine."""

    def __init__(self, settings: Optional[EngineSettings] = None) -> None:
        self.settings = settings or get_settings()

    def _build_deterministic_explanation(
        self, req: AssistantChatRequest
    ) -> Tuple[str, str, List[str], List[str]]:
        """Generate rich, context-aware plain + scientific explanations with multi-turn memory."""
        prior_text = " ".join(t.content.lower() for t in req.history[-4:]) if req.history else ""
        q_low = req.question.lower()
        combined_low = f"{q_low} {prior_text}" if len(q_low.split()) <= 6 else q_low
        ctx = req.active_context or {}

        if any(k in combined_low for k in ("finops", "budget", "cost", "402", "tab 4", "gpu", "nim")):
            plain = (
                "👤 IN EVERYDAY TERMS (DEEP EXPLANATION):\n"
                "1. Why Pharmaceutical Budgets Run Out: In modern drug development, every clinical trial (such as 'STUDY-ONCO-KRAS-2026') "
                "operates on a strictly approved research grant (for example, $2,500.00). When research teams use AI agents to summarize "
                "hundreds of patient reports or run Quantum simulations on candidate molecules, an unmonitored script or an overnight loop "
                "can accidentally consume thousands of dollars in cloud API credits in a few hours.\n\n"
                "2. How Tab 4 Acts as a Financial Circuit-Breaker: Tab 4 is a dedicated 'smart bank account' for each clinical study. "
                "Every time you run a Clinical Synthesis (Tab 1) or a Quantum Molecule Screen (Tab 2), this module calculates the exact cost "
                "in fractions of a cent and deducts it from that study's grant. If a study's remaining budget drops below the cost of the next run, "
                "the system automatically blocks the request with an HTTP 402 Financial Guardrail alert before a single cent is overspent.\n\n"
                "3. Real Hardware Cost Savings (70.5% Reduction): Instead of paying expensive per-seat SaaS subscriptions ($60/user/month) "
                "or uncalibrated cloud API rates, this platform routes workloads through your centralized LiteLLM Gateway and ephemeral Spot L4 GPUs "
                "($0.28/hour vs. $0.95/hour On-Demand), saving over 70% of the research grant."
            )
            sci = (
                "🔬 FOR THE SCIENTIST & FINOPS ARCHITECT (DEEP DIVE):\n"
                "1. Granular Per-Study Metering Model: `ClinicalStudyBudgetController` (backed by ACID SQLite transactions in `src/finops/study_budget.py`) "
                "enforces strict R&D Chargeback/Showback per `clinical_study_id`. It meters two distinct scientific compute vectors:\n"
                "   • Clinical NLP & Multi-Judge Vector: `Cost_clinical = ((prompt_tokens + completion_tokens) / 1000) * (C_synth + C_3x_judges)`.\n"
                "   • Quantum Statevector Volume Vector: `Cost_quantum = C_base + (num_qubits * circuit_depth) * C_qubit_depth`.\n\n"
                "2. Pre-Flight & Post-Flight HTTP 402 Enforcement: Prior to invoking Tier-1 (NVIDIA NIM Direct) or Tier-2 (LiteLLM Gateway :4001), "
                "`synthesize_clinical_protocol` performs a pre-flight token estimation check against `remaining_budget_usd`. If `tx_cost > remaining_budget_usd`, "
                "`StudyBudgetExceededError` is raised and mapped to an HTTP 402 (`CLINICAL_STUDY_GRANT_BUDGET_EXCEEDED`) response.\n\n"
                "3. Ephemeral Spot GPU NIM Economics: Integrates benchmark telemetry from `nvidia-nim-enterprise-patterns` comparing GCP `g2-standard` "
                "Spot L4 24GB GPUs ($0.28/hr with <25s warm TensorRT-LLM engine cache recovery) against On-Demand ($0.95/hr) and proprietary token APIs (3.4x multiplier)."
            )
            steps = [
                "Step 1 — Inspect Active Study Grants: Open Tab 4 ('4. Pharma & Quantum FinOps') from the Left Menu to view Allocated Grant, Total Spend, Remaining Cap, and Spot GPU savings for every clinical study.",
                "Step 2 — Adjust or Top-Up a Study Budget: In the 'Interactive R&D Study Grant Allocation' panel, enter a study ID (e.g., STUDY-ONCO-KRAS-2026) and click 'Set $2,500 Standard Grant', 'Set $5,000 Phase II Grant', or type a custom USD amount and click 'Allocate / Update Study Grant Cap'.",
                "Step 3 — Trigger the Live HTTP 402 Circuit-Breaker: Click the red button 'Simulate Runaway Spend (Test HTTP 402 Guardrail)'. This allocates a micro-grant ($0.0005) to STUDY-GUARDRAIL-DEMO-2026 and attempts a synthesis run, immediately demonstrating the live HTTP 402 block.",
                "Step 4 — Bill Runs & Compare GPU ROI: On any study card, click 'Run Clinical Synthesis' or 'Screen Molecule' to bill new R&D runs to that grant, or click 'Compare Spot L4 GPU ROI' on Ecosystem Card 4 to inspect the 100-hour Phase II hardware benchmark."
            ]
        elif any(k in combined_low for k in ("fda", "part 11", "ledger", "sha-256", "hitl", "sign", "tab 3", "judge")):
            plain = (
                "👤 IN EVERYDAY TERMS (DEEP EXPLANATION):\n"
                "1. The Core Problem in Medical AI: If an AI summarizes a clinical trial report and accidentally leaves out a dangerous side effect "
                "(like a severe immune reaction or liver toxicity), patients could be harmed. Furthermore, regulators like the US FDA and European EMA "
                "forbid 'black-box' systems where records can be silently edited or deleted after the fact.\n\n"
                "2. How the 3 AI Judges Protect Patient Safety (Tab 1): Instead of trusting a single AI answer, this platform sends every clinical summary "
                "to 3 independent digital inspectors ('Judges') at the exact same time:\n"
                "   • Judge 1 (Groundedness): Checks that every paragraph cites the exact source section ([CIT-P1], [CIT-P2]) so nothing is made up.\n"
                "   • Judge 2 (Pharmacovigilance Safety): Compares every side effect in the original hospital note against the AI summary to guarantee 100% recall.\n"
                "   • Judge 3 (GxP Regulatory Tone): Ensures no speculative or off-label drug dosing is suggested.\n\n"
                "3. How the FDA Vault & Doctor Signature Work (Tab 3): Every result is locked into a digital ledger where each record's cryptographic fingerprint "
                "(SHA-256 hash) includes the fingerprint of the record before it. If a high-risk event (SUSAR) is detected, the system pauses autonomous approval "
                "and requires a real physician (Medical Monitor) to apply a legally binding electronic signature in Tab 3."
            )
            sci = (
                "🔬 FOR THE SCIENTIST & GXP AUDITOR (DEEP DIVE):\n"
                "1. Calibrated Multi-Judge Consensus Mathematics (`src/evaluators/multi_judge_consensus.py`): Executes `ClinicalGroundednessJudge` (w=0.40), "
                "`PharmacovigilanceSafetyJudge` (w=0.40), and `GxPComplianceJudge` (w=0.20) concurrently via `asyncio.gather`. Computes the weighted mean "
                "`μ_w = Σ w_i s_i`, the weighted score variance `σ² = Σ w_i (s_i - μ_w)²`, and applies a variance penalty factor `λ = 0.50`:\n"
                "   `Consensus_Score = clamp(μ_w - λ * σ², 0.0, 1.0)`.\n"
                "   If `Consensus_Score < 0.95` or `PharmacovigilanceSafetyJudge` detects a SUSAR / Grade 4-5 toxicity trigger, `governance_status` transitions "
                "deterministically to `PENDING_HITL_MEDICAL_REVIEW`.\n\n"
                "2. FDA 21 CFR Part 11 Cryptographic Hash Chaining (`src/compliance/fda_part11_ledger.py`): Enforces §11.10 (tamper-evident audit trails), "
                "§11.50 (signature manifestations), and §11.70 (signature/record linking). Each block's digest is computed as:\n"
                "   `H_n = SHA256(H_{n-1} || Timestamp_UTC || Study_ID || Scrubbed_Prompt_SHA256 || Output || Score || Reviewer_Sig_SHA256)`.\n\n"
                "3. Mathematical Tamper Verification: Calling `GET /v1/audit/verify-integrity` recomputes every SHA-256 digest from `GENESIS_HASH` (`0x00..00`). "
                "Any unauthorized SQLite mutation breaks the chain and pinpoints the exact compromised `record_id`."
            )
            steps = [
                "Step 1 — Trigger a High-Risk Safety Escalation: In Tab 1 ('1. Clinical GxP & Judges'), click the 3rd preset ('High-Risk SUSAR • Triggers HITL Review') and click 'Run HIPAA Scrubber + Clinical Synthesis + 3x GxP Audit'.",
                "Step 2 — Inspect the 3 Judge Cards: Observe how Judge 2 (PharmacovigilanceSafetyJudge) flags the Grade 4 Cytokine Release Syndrome (SUSAR) and sets status to PENDING_HITL_MEDICAL_REVIEW.",
                "Step 3 — Apply an FDA 21 CFR Part 11 Electronic Signature: Switch to Tab 3 ('3. FDA Part 11 Ledger'), click the flagged record in the right-hand table, verify your Medical Reviewer ID (e.g., MD-ROCHE-4491) and Signature Meaning (§11.50), and click 'Append Cryptographic Electronic Signature'.",
                "Step 4 — Prove Zero Database Tampering: Click 'Verify SHA-256 Chain Integrity' in Tab 3 to run a full cryptographic audit from Genesis to the latest signed block."
            ]
        elif any(k in combined_low for k in ("vqe", "smiles", "molecule", "hartree", "binding", "tab 2", "screener")):
            q_ctx = ctx.get("latest_quantum") or {}
            rec = q_ctx.get("target_receptor", "KRAS-G12C")
            dg = q_ctx.get("binding_affinity_kcal_mol", -9.85)
            e0 = q_ctx.get("vqe_ground_state_energy_hartree", -101.42)
            plain = (
                f"👤 IN EVERYDAY TERMS (DEEP EXPLANATION):\n"
                f"1. The Lock-and-Key Analogy in Drug Discovery: Imagine a disease protein like `{rec}` (which drives tumor growth "
                f"or neurodegeneration) as a microscopic 3D lock. A candidate drug molecule (written as a text formula called `SMILES`) "
                f"is a key designed to jam that lock so the disease stops progressing.\n\n"
                f"2. Why Quantum Simulation Matters: Synthesizing and testing thousands of chemical keys in a physical laboratory takes "
                f"years and tens of millions of dollars. Classical computers struggle to accurately simulate how electron clouds interact "
                f"between the drug and the receptor pocket. Tab 2 uses a Quantum Variational simulator to calculate the lowest stable energy "
                f"of the drug-receptor pair in seconds.\n\n"
                f"3. How to Read Your Numbers: Your screened molecule on `{rec}` reached a ground-state energy of `{e0} Hartrees` and a "
                f"Binding Affinity (ΔG) of `{dg} kcal/mol`. In pharmacology, a more negative ΔG means a stronger, tighter bond: values "
                f"below `-9.5 kcal/mol` indicate a high-potency lead candidate ready for laboratory validation."
            )
            sci = (
                f"🔬 FOR THE SCIENTIST & QUANTUM ARCHITECT (DEEP DIVE):\n"
                f"1. Active-Space Hamiltonian Mapping (`src/agents/quantum_molecular_screener.py`): Maps the canonical SMILES ligand and "
                f"target receptor `{rec}` into a reduced active-space electronic Hamiltonian:\n"
                f"   `H = E_core + Σ_i h_i Z_i + Σ_<i,j> J_ij Z_i Z_j` over `N` qubits (`dim(H) = 2^N`).\n\n"
                f"2. Hardware-Efficient Parameterized Ansatz: Constructs `L` variational layers of single-qubit rotations `RY(θ_{{l,q}}) RZ(φ_{{l,q}})` "
                f"followed by a linear nearest-neighbor `CNOT(q, q+1)` entanglement ladder. Supports dual-backend execution: exact pure-Python "
                f"complex statevector simulation (`PurePythonStatevectorSimulator`) out-of-the-box, or `Qiskit` `Statevector` acceleration.\n\n"
                f"3. VQE Convergence & ΔG Derivation: Across variational iterations, the optimizer minimizes `<ψ(θ,φ)|H|ψ(θ,φ)> → E_0 = {e0} Ha`. "
                f"From the variational relaxation drop `ΔE = E_init - E_0` and active orbital count, the receptor binding free energy is estimated "
                f"at `ΔG = {dg} kcal/mol`, logged to the FDA Part 11 ledger with full gate/depth telemetry."
            )
            steps = [
                "Step 1 — Select a Reference Drug Ligand: Open Tab 2 ('2. Quantum VQE Screener') and click one of the 3 validated presets (Sotorasib for KRAS-G12C, Osimertinib for EGFR-T790M, or Verubecestat for BACE1) or paste any canonical SMILES string.",
                "Step 2 — Configure Quantum Active Space: Set 'Active-Space Qubits (2-12)' (e.g., 6 or 8 qubits) and 'RY/RZ + CNOT Layers (1-8)' (e.g., 3 or 4 layers) to control circuit depth and entanglement capacity.",
                "Step 3 — Run the VQE Statevector Simulation: Click 'Execute Hybrid Quantum VQE Screening' and watch the 4-stage animated pipeline stepper progress through Hamiltonian mapping, Ansatz construction, VQE minimization, and FDA ledger attestation.",
                "Step 4 — Analyze Telemetry & Trajectory: Inspect the VQE Ground Energy (Ha), Binding Affinity ΔG (kcal/mol), Dominant Bitstring |ψ⟩, the SVG convergence curve, and the ASCII quantum circuit diagram."
            ]
        else:
            plain = (
                "👤 IN EVERYDAY TERMS (DEEP EXPLANATION):\n"
                "1. What This Platform Does: This application is an all-in-one safety, discovery, and budget control center for creating new medicines using AI and Quantum computing.\n\n"
                "2. How the 4 Modules Work Together:\n"
                "   • Module 1 (Clinical GxP & 3x Judges): Automatically erases private patient information (names, SSNs, hospital IDs) from clinical trial notes, summarizes the medical findings, and has 3 independent AI inspectors verify that zero side effects were missed.\n"
                "   • Module 2 (Quantum VQE Screener): Tests how strongly a candidate drug molecule locks onto a disease protein using quantum simulation, saving months of laboratory work.\n"
                "   • Module 3 (FDA Part 11 Ledger): Locks every AI and Quantum result into a tamper-proof digital vault (SHA-256 chain) and allows a real doctor to electronically sign off on high-risk findings.\n"
                "   • Module 4 (Pharma & Quantum FinOps): Tracks the exact research budget for each clinical study and automatically stops runaway AI/Quantum costs before they exceed the grant."
            )
            sci = (
                "🔬 FOR THE SCIENTIST & PRINCIPAL ARCHITECT (DEEP DIVE):\n"
                "1. End-to-End Regulated Architecture: `quantum-biomed-research-engine` is a 12-Factor, Dual-Mode enterprise platform (FastAPI + Pydantic v2 + React 18 + SQLite K3s PVC) engineered for ICH E6(R3) GxP, HIPAA Safe Harbor, EU AI Act Annex III, and FDA 21 CFR Part 11 compliance.\n\n"
                "2. Technical Pipeline Integration:\n"
                "   • Privacy & Synthesis: Regex/rule-based `PHIScrubber` computes pre/post SHA-256 digests before routing scrubbed text through a 3-Tier LLM gateway (Tier 1: NVIDIA NIM TensorRT-LLM → Tier 2: LiteLLM :4001 → Tier 3: Deterministic GxP Engine).\n"
                "   • Multi-Judge Consensus & Quantum VQE: Runs 3 concurrent judges via `asyncio.gather` (`Consensus = μ_w - λσ² ≥ 0.95`) alongside a `$2^N$` complex statevector VQE screener (`RY/RZ + CNOT`).\n"
                "   • Cryptographic Audit & FinOps: Persists SHA-256 hash-chained blocks with §11.50 HITL e-signatures and enforces HTTP 402 study grant caps."
            )
            steps = [
                "Step 1 (Module 1 — Clinical GxP & Judges): Pick a clinical trial preset, select an LLM model from the Left Sidebar, and click 'Run HIPAA Scrubber + Clinical Synthesis + 3x GxP Audit'.",
                "Step 2 (Module 2 — Quantum VQE Screener): Select a SMILES drug candidate (e.g., Sotorasib) and click 'Execute Hybrid Quantum VQE Screening' to compute E_0 (Ha) and ΔG (kcal/mol).",
                "Step 3 (Module 3 — FDA Part 11 Ledger): Click any record in the SHA-256 ledger to append a Medical Reviewer HITL Electronic Signature and click 'Verify SHA-256 Chain Integrity'.",
                "Step 4 (Module 4 — Pharma & Quantum FinOps): Allocate or top-up a clinical study grant, test the live HTTP 402 guardrail, and compare Spot L4 GPU NIM savings."
            ]

        if req.persona_mode == "plain":
            followups = [
                "Explain in simple terms how the 3 AI Judges protect patient safety",
                "Give me an everyday analogy for how Quantum VQE drug screening works",
                "Why is the FDA digital vault (Tab 3) important for patients and doctors?",
                "How does the study budget circuit-breaker (Tab 4) save money?"
            ]
        elif req.persona_mode == "scientist":
            followups = [
                "Detail the mathematical formula of the 3-Judge consensus & variance penalty",
                "Explain the N-qubit VQE Hamiltonian, RY/RZ + CNOT ansatz & ΔG derivation",
                "How does the FDA 21 CFR Part 11 SHA-256 hash chain detect SQLite tampering?",
                "Compare Tier-1 Spot L4 GPU NIM TensorRT-LLM vs. Tier-2 LiteLLM routing"
            ]
        elif req.persona_mode == "steps":
            followups = [
                "Walk me step-by-step through triggering and signing a High-Risk SUSAR alert",
                "Show me step-by-step how to run a Quantum VQE screen and read the circuit",
                "How do I test the HTTP 402 budget guardrail step-by-step in Tab 4?",
                "How do I verify the SHA-256 audit chain and inspect the Swagger API?"
            ]
        else:
            followups = [
                "How do I use the 4 tabs step-by-step for a live demo?",
                "Explain the Quantum VQE Molecular Screener (SMILES, Hartrees & ΔG)",
                "What does Pharma & Quantum Grant FinOps do in Tab 4?",
                "How do the 3 GxP Judges and FDA 21 CFR Part 11 SHA-256 chain work?",
            ]
        return plain, sci, steps, followups

    async def answer_question(self, req: AssistantChatRequest) -> AssistantChatResponse:
        """Answer user question in plain everyday language, scientific language, or both."""
        plain, sci, steps, followups = self._build_deterministic_explanation(req)
        force_offline = req.preferred_model == "deterministic-offline"
        should_try_live = (not force_offline) and (
            self.settings.llm_live_mode or bool(req.preferred_model and req.preferred_model.strip())
        )

        turn_num = len(req.history) // 2 + 1
        if should_try_live and self.settings.litellm_base_url and self.settings.litellm_api_key:
            model_id = (req.preferred_model or self.settings.litellm_primary_model).removeprefix("openai/")
            try:
                import httpx

                ctx_str = json.dumps(req.active_context or {}, default=str)[:1800]
                track_instructions = {
                    "plain": (
                        "The user has locked the conversation strictly to Track 1: EVERYDAY PLAIN LANGUAGE. "
                        "Provide a comprehensive, detailed 4-to-5 paragraph explanation using vivid everyday analogies, "
                        "real-world examples, and clear business/patient impact without heavy math jargon."
                    ),
                    "scientist": (
                        "The user has locked the conversation strictly to Track 2: SCIENTIST & GXP PRINCIPAL ARCHITECT DEEP-DIVE. "
                        "Provide a rigorous, comprehensive 4-to-5 paragraph technical and mathematical deep-dive covering "
                        "Hamiltonians, VQE RY/RZ+CNOT ansätze, ΔG (kcal/mol), ICH E6(R3), FDA 21 CFR Part 11 (§11.10/§11.50/§11.70) "
                        "SHA-256 hash chaining, and 3-Judge consensus equations."
                    ),
                    "steps": (
                        "The user has locked the conversation strictly to Track 3: STEP-BY-STEP PRACTICAL OPERATIONAL GUIDE. "
                        "Provide a detailed, numbered step-by-step operational walkthrough (6-8 detailed steps) explaining "
                        "exactly what to click, what inputs to test, and how to interpret every metric on screen."
                    ),
                    "dual": (
                        "Provide a comprehensive, multi-paragraph explanation in both Plain Language and Scientific Deep-Dive."
                    ),
                }
                sys_msg = (
                    "You are Dr. Helix, the AI Guide & Principal R&D Copilot for the Quantum BioMed Research & GxP Governance Engine. "
                    "Maintain multi-turn conversational continuity with prior messages. "
                    f"{track_instructions.get(req.persona_mode, track_instructions['dual'])} "
                    "Answer in the same language as the user's question (English or Romanian)."
                )
                llm_messages: List[Dict[str, str]] = [{"role": "system", "content": sys_msg}]
                for h_turn in req.history[-8:]:
                    llm_messages.append({"role": h_turn.role, "content": h_turn.content[:1500]})
                user_msg = (
                    f"User Question (Turn #{turn_num}): {req.question}\n"
                    f"Requested Persona Mode: {req.persona_mode}\n"
                    f"Live Application Context: {ctx_str}"
                )
                llm_messages.append({"role": "user", "content": user_msg})
                async with httpx.AsyncClient(timeout=httpx.Timeout(25.0, connect=3.5)) as client:
                    resp = await client.post(
                        f"{self.settings.litellm_base_url.rstrip('/')}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.settings.litellm_api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": model_id,
                            "messages": llm_messages,
                            "temperature": 0.2,
                        },
                    )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    if content:
                        if req.persona_mode == "steps":
                            parsed_steps = [
                                line.strip()
                                for line in content.split("\n")
                                if line.strip()
                            ]
                            return AssistantChatResponse(
                                question=req.question,
                                persona_mode=req.persona_mode,
                                plain_language_summary=plain,
                                scientific_deep_dive=sci,
                                step_by_step_guide=parsed_steps if len(parsed_steps) >= 2 else steps,
                                suggested_followups=followups,
                                execution_tier="TIER_2_LITELLM_GATEWAY",
                                model_used=model_id,
                                turn_count=turn_num,
                            )
                        return AssistantChatResponse(
                            question=req.question,
                            persona_mode=req.persona_mode,
                            plain_language_summary=content if req.persona_mode != "scientist" else plain,
                            scientific_deep_dive=content if req.persona_mode == "scientist" else sci,
                            step_by_step_guide=steps,
                            suggested_followups=followups,
                            execution_tier="TIER_2_LITELLM_GATEWAY",
                            model_used=model_id,
                            turn_count=turn_num,
                        )
            except Exception as exc:
                logger.warning("Assistant live gateway call fell back to deterministic guide: %s", exc)

        return AssistantChatResponse(
            question=req.question,
            persona_mode=req.persona_mode,
            plain_language_summary=plain,
            scientific_deep_dive=sci,
            step_by_step_guide=steps,
            suggested_followups=followups,
            execution_tier="TIER_3_DETERMINISTIC_GUIDE",
            model_used="deterministic-biomed-guide-v1",
            turn_count=turn_num,
        )

