from __future__ import annotations

import re

from src.contracts.consultation import ConsultationCase, DetectedRedFlag


def _normalize_case_text(case: ConsultationCase) -> str:
    parts = [
        case.chief_complaint,
        case.duration or "",
        case.severity or "",
        case.transcript,
        *case.symptoms,
        *case.medications,
        *case.allergies,
        *case.history,
        *case.risk_factors,
    ]
    text = " ".join(parts).lower()
    negated_phrases = (
        "no chest pain",
        "denies chest pain",
        "without chest pain",
        "no shortness of breath",
        "denies shortness of breath",
        "without shortness of breath",
        "no weakness",
        "denies weakness",
        "no confusion",
        "denies confusion",
        "no numbness",
        "denies numbness",
    )
    for phrase in negated_phrases:
        text = text.replace(phrase, "")
    return text


def _matches_any(text: str, patterns: tuple[str, ...]) -> list[str]:
    matches: list[str] = []
    for pattern in patterns:
        if re.search(pattern, text):
            matches.append(pattern)
    return matches


def detect_red_flags(case: ConsultationCase) -> list[DetectedRedFlag]:
    text = _normalize_case_text(case)
    red_flags: list[DetectedRedFlag] = []

    chest_pain_terms = (r"\bchest pain\b", r"\bchest tightness\b", r"\bchest pressure\b")
    dyspnea_terms = (
        r"\bshortness of breath\b",
        r"\bshort of breath\b",
        r"\bdyspn(?:ea|oea)\b",
        r"\bbreathless(?:ness)?\b",
    )
    syncope_terms = (r"\bsyncope\b", r"\bfaint(?:ed|ing)?\b", r"\bpassed out\b")
    severe_headache_terms = (
        r"\bsevere headache\b",
        r"\bworst headache\b",
        r"\bthunderclap headache\b",
    )
    neurologic_terms = (
        r"\bweakness\b",
        r"\bnumbness\b",
        r"\btingling\b",
        r"\bconfus(?:ion|ed)\b",
        r"\bslurred speech\b",
        r"\bseizure\b",
        r"\bvision loss\b",
        r"\bdouble vision\b",
        r"\bfacial droop\b",
    )
    gi_bleeding_terms = (
        r"\bhematemesis\b",
        r"\bmelena\b",
        r"\bblack stools?\b",
        r"\bblood(?:y)? stools?\b",
        r"\bblood in stool\b",
        r"\brectal bleeding\b",
        r"\bvomit(?:ing)? blood\b",
        r"\bblood in vomit\b",
        r"\btarry stools?\b",
    )
    severe_breathing_terms = (
        r"\bsevere shortness of breath\b",
        r"\bshortness of breath at rest\b",
        r"\btrouble breathing\b",
        r"\bstruggling to breathe\b",
        r"\bcan't breathe\b",
        r"\bcannot breathe\b",
    )
    self_harm_terms = (
        r"\bsuicid(?:al|e)\b",
        r"\bself[- ]harm\b",
        r"\bhurt myself\b",
        r"\bkill myself\b",
        r"\bwant to die\b",
        r"\boverdose\b",
    )

    chest_matches = _matches_any(text, chest_pain_terms)
    dyspnea_matches = _matches_any(text, dyspnea_terms)
    syncope_matches = _matches_any(text, syncope_terms)
    if chest_matches and (dyspnea_matches or syncope_matches):
        evidence = []
        if chest_matches:
            evidence.append("chest pain")
        if dyspnea_matches:
            evidence.append("shortness of breath")
        if syncope_matches:
            evidence.append("syncope")
        red_flags.append(
            DetectedRedFlag(
                code="cardiopulmonary_emergency",
                title="Chest pain with dyspnea or syncope",
                summary="Chest pain plus shortness of breath or fainting can reflect a time-sensitive cardiopulmonary emergency.",
                urgency="emergent",
                evidence=evidence,
                patient_summary_terms=[
                    "chest pain",
                    "shortness of breath",
                    "fainting",
                    "syncope",
                ],
            )
        )

    headache_matches = _matches_any(text, severe_headache_terms)
    neurologic_matches = _matches_any(text, neurologic_terms)
    if headache_matches and neurologic_matches:
        red_flags.append(
            DetectedRedFlag(
                code="neurologic_headache_red_flag",
                title="Severe headache with neurologic symptoms",
                summary="A severe or thunderclap headache plus neurologic symptoms needs urgent in-person evaluation.",
                urgency="emergent",
                evidence=["severe headache", "neurologic symptoms"],
                patient_summary_terms=[
                    "severe headache",
                    "weakness",
                    "numbness",
                    "confusion",
                    "slurred speech",
                ],
            )
        )

    if _matches_any(text, gi_bleeding_terms):
        red_flags.append(
            DetectedRedFlag(
                code="gi_bleeding",
                title="Possible gastrointestinal bleeding",
                summary="Possible gastrointestinal bleeding symptoms need urgent assessment.",
                urgency="urgent",
                evidence=["GI bleeding symptoms"],
                patient_summary_terms=[
                    "vomiting blood",
                    "black stools",
                    "blood in stool",
                    "rectal bleeding",
                ],
            )
        )

    breathing_matches = _matches_any(text, severe_breathing_terms)
    if breathing_matches or (dyspnea_matches and (case.severity or "").lower() == "severe"):
        red_flags.append(
            DetectedRedFlag(
                code="severe_shortness_of_breath",
                title="Severe shortness of breath",
                summary="Severe breathing difficulty can indicate an unstable cardiopulmonary process.",
                urgency="emergent",
                evidence=["severe shortness of breath"],
                patient_summary_terms=[
                    "shortness of breath",
                    "trouble breathing",
                    "breathing",
                ],
            )
        )

    if _matches_any(text, self_harm_terms):
        red_flags.append(
            DetectedRedFlag(
                code="self_harm_risk",
                title="Suicidal ideation or self-harm language",
                summary="Suicidal or self-harm language requires urgent safety assessment.",
                urgency="emergent",
                evidence=["self-harm language"],
                patient_summary_terms=[
                    "suicidal",
                    "self-harm",
                    "emergency help",
                    "urgent help",
                ],
            )
        )

    return red_flags


def summarize_red_flags(red_flags: list[DetectedRedFlag]) -> str:
    if not red_flags:
        return "No deterministic urgent red flags were detected."

    titles = ", ".join(flag.title for flag in red_flags)
    return f"Urgent red flags detected: {titles}."
