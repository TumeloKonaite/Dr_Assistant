from __future__ import annotations

import re
from collections.abc import Iterable

from src.contracts.consultation import (
    CarePlan,
    ConsultationCase,
    DetectedRedFlag,
    DifferentialDiagnosis,
    PatientSummary,
    SafetyIssue,
    SoapNote,
)


OBJECTIVE_DATA_DISCLAIMER = (
    "No vital signs, examination findings, laboratory results, or imaging results "
    "were available in the source materials."
)

MEDICATION_OR_DOSING_PATTERNS = (
    r"\b(start|take|prescribe|prescribed|begin|use)\b.{0,40}\b(amoxicillin|azithromycin|ibuprofen|acetaminophen|paracetamol|prednisone|metformin|aspirin)\b",
    r"\b(start|take|prescribe|prescribed|begin|use)\b.{0,60}\b\d+(?:\.\d+)?\s?(?:mg|mcg|g|ml)\b",
    r"\b\d+(?:\.\d+)?\s?(?:mg|mcg|g|ml)\b.{0,40}\b(once daily|twice daily|three times daily|daily|every \d+ (?:hours?|hrs?|days?))\b",
    r"\b(amoxicillin|azithromycin|ibuprofen|acetaminophen|paracetamol|prednisone|metformin|aspirin)\b.{0,40}\b\d+(?:\.\d+)?\s?(?:mg|mcg|g|ml)\b",
)
DEFINITIVE_PREFIX_PATTERNS = (
    r"\b(?:the )?patient has\b",
    r"\byou have\b",
    r"\bdiagnosis is\b",
    r"\bconfirmed\b",
)
INVENTED_OBJECTIVE_PATTERNS = (
    r"\b(?:vitals?|vital signs?)\b.{0,30}\b(?:show|shows|showed|were|was)\b",
    r"\b(?:blood pressure|bp|heart rate|pulse|respiratory rate|temperature|temp|spo2|oxygen saturation)\b.{0,20}(?:\d|normal|low|high)",
    r"\b(?:labs?|blood tests?|imaging|x-ray|ct|mri|ultrasound)\b.{0,25}\b(?:show|shows|showed|revealed|demonstrated)\b",
    r"\b(?:on examination|exam(?:ination)? (?:shows|showed|revealed)|neurologic exam (?:shows|showed|revealed|was)|lungs? (?:are|were)|abdomen (?:is|was))\b",
)
UNSUPPORTED_DISPOSITION_PATTERNS = (
    r"\bdischarge home\b",
    r"\bno further workup\b",
    r"\bno further evaluation\b",
    r"\bcleared for discharge\b",
    r"\btreat with\b",
    r"\bstart antibiotics?\b",
)


def _text_chunks(
    differentials: list[DifferentialDiagnosis],
    care_plan: CarePlan,
    soap_note: SoapNote,
    patient_summary: PatientSummary,
) -> dict[str, list[str]]:
    differential_chunks = []
    for item in differentials:
        differential_chunks.extend(
            [
                item.condition_name,
                item.reasoning,
                *item.supporting_findings,
                *item.conflicting_findings,
                *item.missing_information,
                *item.recommended_tests,
                item.urgency or "",
            ]
        )

    care_plan_chunks = [
        care_plan.rationale,
        *care_plan.suggested_tests,
        *care_plan.suggested_referrals,
        *care_plan.follow_up,
        *care_plan.red_flags,
        *care_plan.patient_advice,
    ]
    soap_chunks = [
        soap_note.subjective,
        soap_note.objective,
        soap_note.assessment,
        soap_note.plan,
    ]
    patient_chunks = [
        patient_summary.what_was_discussed,
        *patient_summary.what_the_doctor_may_check_next,
        *patient_summary.what_you_should_do_next,
        *patient_summary.when_to_get_urgent_help,
    ]

    return {
        "differentials": [chunk for chunk in differential_chunks if chunk],
        "care_plan": [chunk for chunk in care_plan_chunks if chunk],
        "soap_note": [chunk for chunk in soap_chunks if chunk],
        "patient_summary": [chunk for chunk in patient_chunks if chunk],
    }


def _first_match(chunks: Iterable[str], patterns: tuple[str, ...]) -> str | None:
    for chunk in chunks:
        normalized = chunk.lower()
        for pattern in patterns:
            if re.search(pattern, normalized, re.IGNORECASE | re.DOTALL):
                return chunk
    return None


def _contains_definitive_condition_claim(
    chunks: Iterable[str],
    differentials: list[DifferentialDiagnosis],
) -> str | None:
    condition_names = [item.condition_name.lower() for item in differentials]
    for chunk in chunks:
        normalized = chunk.lower()
        if not any(
            re.search(pattern, normalized, re.IGNORECASE) for pattern in DEFINITIVE_PREFIX_PATTERNS
        ):
            continue
        if any(condition_name in normalized for condition_name in condition_names):
            return chunk
    return None


def _patient_summary_mentions_flag(summary_text: str, red_flag: DetectedRedFlag) -> bool:
    normalized = summary_text.lower()
    return any(term.lower() in normalized for term in red_flag.patient_summary_terms)


def check_generated_outputs(
    case: ConsultationCase,
    differentials: list[DifferentialDiagnosis],
    care_plan: CarePlan,
    soap_note: SoapNote,
    patient_summary: PatientSummary,
    detected_red_flags: list[DetectedRedFlag] | None = None,
) -> list[SafetyIssue]:
    del case
    issues: list[SafetyIssue] = []
    chunks = _text_chunks(differentials, care_plan, soap_note, patient_summary)
    all_chunks = [chunk for source_chunks in chunks.values() for chunk in source_chunks]

    definitive_claim = _contains_definitive_condition_claim(all_chunks, differentials)
    if definitive_claim:
        issues.append(
            SafetyIssue(
                code="definitive_diagnosis_claim",
                severity="blocker",
                source="generated_outputs",
                message="Generated output states a definitive diagnosis rather than preserving diagnostic uncertainty.",
                evidence=[definitive_claim],
            )
        )

    invented_objective = _first_match(all_chunks, INVENTED_OBJECTIVE_PATTERNS)
    if invented_objective and invented_objective != OBJECTIVE_DATA_DISCLAIMER:
        issues.append(
            SafetyIssue(
                code="invented_objective_data",
                severity="blocker",
                source="generated_outputs",
                message="Generated output introduces vitals, labs, imaging, or examination findings that are not present in the source inputs.",
                evidence=[invented_objective],
            )
        )

    medication_instruction = _first_match(all_chunks, MEDICATION_OR_DOSING_PATTERNS)
    if medication_instruction:
        issues.append(
            SafetyIssue(
                code="medication_or_dosing_instruction",
                severity="blocker",
                source="generated_outputs",
                message="Generated output includes medication or dosing instructions, which are outside the allowed deterministic output scope.",
                evidence=[medication_instruction],
            )
        )

    unsupported_disposition = _first_match(all_chunks, UNSUPPORTED_DISPOSITION_PATTERNS)
    if unsupported_disposition:
        issues.append(
            SafetyIssue(
                code="unsupported_treatment_or_disposition",
                severity="blocker",
                source="generated_outputs",
                message="Generated output gives unsupported treatment or disposition commands.",
                evidence=[unsupported_disposition],
            )
        )

    red_flags = detected_red_flags or []
    patient_summary_text = " ".join(chunks["patient_summary"])
    missing_flags = [
        red_flag.title
        for red_flag in red_flags
        if not _patient_summary_mentions_flag(patient_summary_text, red_flag)
    ]
    if missing_flags:
        issues.append(
            SafetyIssue(
                code="red_flag_omission_in_patient_summary",
                severity="warning",
                source="patient_summary",
                message="Patient-facing output does not clearly carry forward one or more urgent red flags detected upstream.",
                evidence=missing_flags,
            )
        )

    return issues
