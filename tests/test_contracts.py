import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.contracts import (
    CarePlan,
    ClinicalReasoningOutput,
    ConsultationCase,
    DifferentialDiagnosis,
    FinalConsultationBundle,
    RetrievedCondition,
    SoapNote,
)


FIXTURE_PATH = Path("tests/fixtures/final_consultation_bundle.example.json")


def load_fixture_payload() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_consultation_case_validates_and_strips_whitespace():
    case = ConsultationCase(
        chief_complaint="  Headache  ",
        symptoms=["headache", "photophobia"],
        transcript="  Patient reports a severe headache since this morning.  ",
    )

    assert case.chief_complaint == "Headache"
    assert case.transcript == "Patient reports a severe headache since this morning."
    assert case.medications == []
    assert case.allergies == []


def test_all_contract_models_accept_valid_payloads():
    case_payload = {
        "patient_id": "P-2001",
        "chief_complaint": "Abdominal pain",
        "symptoms": ["abdominal pain", "nausea"],
        "duration": "1 day",
        "severity": "moderate",
        "medications": ["omeprazole"],
        "allergies": ["sulfa"],
        "history": ["gastritis"],
        "risk_factors": ["NSAID use"],
        "transcript": "Patient reports abdominal pain and nausea since yesterday.",
    }
    retrieved_condition_payload = {
        "name": "gastritis",
        "description": "Inflammation of the stomach lining.",
        "matched_symptoms": ["abdominal pain", "nausea"],
        "score": 0.81,
    }
    differential_payload = {
        "condition_name": "gastritis",
        "likelihood": "moderate",
        "reasoning": "Symptoms and history make gastritis a plausible explanation, but the available information is limited.",
        "supporting_findings": ["abdominal pain", "nausea", "history of gastritis"],
        "conflicting_findings": ["No abdominal exam findings are available."],
        "missing_information": ["GI bleeding symptoms"],
        "recommended_tests": ["CBC"],
        "urgency": None,
    }
    care_plan_payload = {
        "suggested_tests": ["CBC"],
        "suggested_referrals": ["Primary care"],
        "follow_up": ["Follow up within 48 hours if symptoms persist."],
        "red_flags": ["hematemesis", "melena"],
        "patient_advice": ["Seek urgent review if pain worsens or bleeding occurs."],
        "rationale": "The next steps focus on clarifying the cause of abdominal pain while monitoring for bleeding or clinical deterioration.",
    }
    soap_note_payload = {
        "subjective": "Patient reports abdominal pain and nausea.",
        "objective": "No abdominal exam findings available from transcript alone.",
        "assessment": "Gastritis is a possible cause of symptoms.",
        "plan": "Provide supportive care guidance and reassess if symptoms worsen.",
    }

    case = ConsultationCase.model_validate(case_payload)
    retrieved_condition = RetrievedCondition.model_validate(retrieved_condition_payload)
    differential = DifferentialDiagnosis.model_validate(differential_payload)
    care_plan = CarePlan.model_validate(care_plan_payload)
    soap_note = SoapNote.model_validate(soap_note_payload)
    bundle = FinalConsultationBundle.model_validate(
        {
            "case": case_payload,
            "differentials": [differential_payload],
            "care_plan": care_plan_payload,
            "soap_note": soap_note_payload,
            "patient_summary": "Symptoms may be related to stomach irritation and need follow-up if they continue.",
        }
    )

    assert case.chief_complaint == "Abdominal pain"
    assert retrieved_condition.score == 0.81
    assert differential.likelihood == "moderate"
    assert care_plan.follow_up == ["Follow up within 48 hours if symptoms persist."]
    assert soap_note.assessment == "Gastritis is a possible cause of symptoms."
    assert bundle.case.patient_id == "P-2001"

    reasoning_output = ClinicalReasoningOutput.model_validate(
        {
            "differentials": [differential_payload],
            "care_plan": care_plan_payload,
        }
    )

    assert reasoning_output.differentials[0].condition_name == "gastritis"


def test_consultation_case_rejects_extra_fields():
    with pytest.raises(ValidationError, match="extra_forbidden"):
        ConsultationCase(
            chief_complaint="Cough",
            symptoms=["cough"],
            transcript="Persistent cough for one week.",
            unexpected="value",
        )


def test_final_consultation_bundle_rejects_nested_extra_fields():
    payload = load_fixture_payload()
    payload["case"]["unexpected"] = "value"

    with pytest.raises(ValidationError, match="extra_forbidden"):
        FinalConsultationBundle.model_validate(payload)


@pytest.mark.parametrize("likelihood", ["very high", "HIGH", "medium", ""])
def test_differential_diagnosis_rejects_invalid_likelihood(likelihood: str):
    with pytest.raises(ValidationError, match="literal_error"):
        DifferentialDiagnosis(
            condition_name="migraine",
            likelihood=likelihood,
            reasoning="Symptoms are compatible with migraine.",
            supporting_findings=["headache"],
            conflicting_findings=[],
            missing_information=["neurologic exam"],
            recommended_tests=[],
        )


@pytest.mark.parametrize(
    ("factory", "match"),
    [
        (
            lambda: ConsultationCase(
                chief_complaint="",
                symptoms=["cough"],
                transcript="Persistent cough for one week.",
            ),
            "chief_complaint",
        ),
        (
            lambda: ConsultationCase(
                chief_complaint="Cough",
                symptoms=["cough"],
                transcript="",
            ),
            "transcript",
        ),
        (
            lambda: CarePlan(
                suggested_tests=["CBC"],
                suggested_referrals=["Primary care"],
                follow_up=["Follow up within 48 hours."],
                red_flags=["worsening pain"],
                patient_advice=[],
                rationale="",
            ),
            "rationale",
        ),
        (
            lambda: SoapNote(
                subjective="",
                objective="Exam deferred.",
                assessment="Likely viral illness.",
                plan="Supportive care.",
            ),
            "subjective",
        ),
        (
            lambda: SoapNote(
                subjective="Fever and cough.",
                objective="",
                assessment="Likely viral illness.",
                plan="Supportive care.",
            ),
            "objective",
        ),
        (
            lambda: SoapNote(
                subjective="Fever and cough.",
                objective="Exam deferred.",
                assessment="",
                plan="Supportive care.",
            ),
            "assessment",
        ),
        (
            lambda: SoapNote(
                subjective="Fever and cough.",
                objective="Exam deferred.",
                assessment="Likely viral illness.",
                plan="",
            ),
            "plan",
        ),
        (
            lambda: DifferentialDiagnosis(
                condition_name="viral syndrome",
                likelihood="lower",
                reasoning="",
                supporting_findings=["fever"],
                conflicting_findings=[],
                missing_information=["temperature"],
                recommended_tests=[],
            ),
            "reasoning",
        ),
        (
            lambda: FinalConsultationBundle(
                case=ConsultationCase(
                    chief_complaint="Fever",
                    symptoms=["fever"],
                    transcript="Patient reports fever.",
                ),
                differentials=[],
                care_plan=CarePlan(
                    suggested_tests=[],
                    suggested_referrals=[],
                    follow_up=["Monitor symptoms over 24 hours."],
                    red_flags=[],
                    patient_advice=[],
                    rationale="Monitor and reassess if symptoms evolve.",
                ),
                soap_note=SoapNote(
                    subjective="Fever since yesterday.",
                    objective="No exam findings available.",
                    assessment="Likely viral illness.",
                    plan="Hydration and rest.",
                ),
                patient_summary="",
            ),
            "patient_summary",
        ),
    ],
)
def test_required_strings_reject_empty_input(factory, match: str):
    with pytest.raises(ValidationError, match=match):
        factory()


def test_final_consultation_bundle_fixture_validates():
    payload = load_fixture_payload()

    bundle = FinalConsultationBundle.model_validate(payload)

    assert bundle.case.chief_complaint == "Chest pain"
    assert bundle.differentials[0].likelihood == "high"
    assert bundle.care_plan.follow_up[0] == "Arrange urgent same-day in-person assessment."


def test_final_consultation_bundle_round_trips_from_json():
    bundle = FinalConsultationBundle.model_validate_json(
        FIXTURE_PATH.read_text(encoding="utf-8")
    )

    dumped = bundle.model_dump(mode="json")

    assert dumped["case"]["patient_id"] == "P-1024"
    assert dumped["soap_note"]["assessment"] == "Symptoms are concerning for acute coronary syndrome."
    assert dumped["differentials"][1]["condition_name"] == "pulmonary embolism"


def test_consultation_case_schema_exposes_example_json():
    schema = ConsultationCase.model_json_schema()

    assert "example" in schema
    assert schema["example"]["chief_complaint"] == "Chest pain"
