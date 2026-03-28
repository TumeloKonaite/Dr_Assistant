from __future__ import annotations

from src.contracts.consultation import ConsultationCase


def build_case_query(case: ConsultationCase) -> str:
    parts: list[str] = []

    if case.chief_complaint and case.chief_complaint.strip():
        parts.append(f"Chief complaint: {case.chief_complaint.strip()}.")

    cleaned_symptoms = [symptom.strip() for symptom in case.symptoms if symptom.strip()]
    if cleaned_symptoms:
        parts.append(f"Symptoms: {', '.join(cleaned_symptoms)}.")

    if case.duration and case.duration.strip():
        parts.append(f"Duration: {case.duration.strip()}.")

    query = "\n".join(parts).strip()
    if not query:
        raise ValueError(
            "Cannot build retrieval query from empty case. "
            "At least one of chief_complaint, symptoms, or duration must be present."
        )

    return query
