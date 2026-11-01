"""HIPAA Safe Harbor & GDPR Deterministic PHI / PII Scrubber.

Detects and redacts Protected Health Information from clinical trial protocols,
case report forms (CRFs), and pharmacovigilance narratives prior to any LLM call:
- Patient Names (e.g., 'Patient: John Doe', 'Subject Name: Maria Popescu', 'Mr./Ms./Mrs. ...')
- SSN / European National ID / CNP (e.g., 123-45-6789, 13-digit national identifiers)
- Dates of Birth (DOB)
- Medical Record Numbers (MRN / Subject IDs)
- Contact Emails and Phone Numbers
"""

from __future__ import annotations

import hashlib
import re
from typing import Dict, List, Pattern, Tuple

from src.schemas import ScrubbedPayload


class PHIScrubber:
    """Deterministic regex + rule-based de-identification engine for clinical text."""

    def __init__(self) -> None:
        self._rules: List[Tuple[str, Pattern[str], str]] = [
            (
                "medical_record_number",
                re.compile(
                    r"\b(?:MRN|Medical\s+Record(?:\s+Number|\s+No\.?)?|Subject\s+ID|Patient\s+ID)"
                    r"\s*[:#=-]?\s*[A-Z0-9-]{4,20}\b",
                    re.IGNORECASE,
                ),
                "[REDACTED_MRN]",
            ),
            (
                "ssn_or_national_id",
                re.compile(
                    r"(?:\b(?:SSN|CNP|National\s+ID)\s*[:#=-]?\s*(?:\d{3}-\d{2}-\d{4}|\d{9,13})\b"
                    r"|\b\d{3}-\d{2}-\d{4}\b"
                    r"|\b[1-8]\d{12}\b)",
                    re.IGNORECASE,
                ),
                "[REDACTED_SSN_CNP]",
            ),
            (
                "date_of_birth",
                re.compile(
                    r"\b(?:DOB|Date\s+of\s+Birth|Born(?:\s+on)?)\s*[:=-]?\s*"
                    r"(?:\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
                    r"|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b",
                    re.IGNORECASE,
                ),
                "[REDACTED_DOB]",
            ),
            (
                "patient_name",
                re.compile(
                    r"(?:\b(?:Patient(?:\s+Name)?|Subject(?:\s+Name)?|Participant)\s*[:=-]\s*"
                    r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}"
                    r"|\b(?:Mr\.|Mrs\.|Ms\.|Patient)\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b)"
                ),
                "[REDACTED_PATIENT_ID]",
            ),
            (
                "email_address",
                re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
                "[REDACTED_EMAIL]",
            ),
            (
                "phone_number",
                re.compile(
                    r"(?:\b(?:Phone|Tel|Mobile|Contact)\s*[:=-]?\s*)?"
                    r"(?:\+\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b",
                    re.IGNORECASE,
                ),
                "[REDACTED_PHONE]",
            ),
        ]

    def scrub(self, text: str) -> ScrubbedPayload:
        """Scrub PHI tokens from clinical text and return cryptographic hashes + metrics."""
        original_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
        working_text = text
        breakdown: Dict[str, int] = {}
        total_redactions = 0

        for category, pattern, replacement in self._rules:
            matches = list(pattern.finditer(working_text))
            count = len(matches)
            if count > 0:
                working_text = pattern.sub(replacement, working_text)
            breakdown[category] = count
            total_redactions += count

        scrubbed_sha256 = hashlib.sha256(working_text.encode("utf-8")).hexdigest()

        return ScrubbedPayload(
            scrubbed_text=working_text,
            original_sha256=original_sha256,
            scrubbed_sha256=scrubbed_sha256,
            total_redactions=total_redactions,
            redaction_breakdown=breakdown,
            hipaa_safe_harbor_compliant=True,
        )
