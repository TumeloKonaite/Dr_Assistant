from src.contracts.consultation import ConsultationCase
from src.rag.query_builder import build_case_query


def test_build_case_query_combines_fields():
    case = ConsultationCase(
        chief_complaint="Headache",
        symptoms=["fever", "nausea"],
        duration="3 days",
        transcript="Patient reports headache, fever, and nausea for three days.",
    )

    query = build_case_query(case)

    assert "Chief complaint: Headache." in query
    assert "Symptoms: fever, nausea." in query
    assert "Duration: 3 days." in query


def test_build_case_query_skips_empty_fields():
    case = ConsultationCase.model_construct(
        chief_complaint="",
        symptoms=[" cough ", "", "  "],
        duration=None,
        transcript="placeholder transcript",
        patient_id=None,
        severity=None,
        medications=[],
        allergies=[],
        history=[],
        risk_factors=[],
    )

    query = build_case_query(case)

    assert query == "Symptoms: cough."


def test_build_case_query_raises_for_empty_case():
    case = ConsultationCase.model_construct(
        chief_complaint="",
        symptoms=[],
        duration="",
        transcript="placeholder transcript",
        patient_id=None,
        severity=None,
        medications=[],
        allergies=[],
        history=[],
        risk_factors=[],
    )

    try:
        build_case_query(case)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Cannot build retrieval query" in str(exc)
