import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.contracts import (
    CarePlan,
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
        "condition": "gastritis",
        "likelihood": "medium",
        "reasoning": "Symptoms and history are compatible with gastritis.",
        "missing_information": ["GI bleeding symptoms"],
    }
    care_plan_payload = {
        "suggested_tests": ["CBC"],
        "referrals": ["Primary care"],
        "follow_up": "Follow up within 48 hours if symptoms persist.",
        "red_flags": ["hematemesis", "melena"],
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
    assert differential.likelihood == "medium"
    assert care_plan.follow_up == "Follow up within 48 hours if symptoms persist."
    assert soap_note.assessment == "Gastritis is a possible cause of symptoms."
    assert bundle.case.patient_id == "P-2001"


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


@pytest.mark.parametrize("likelihood", ["very high", "HIGH", ""])
def test_differential_diagnosis_rejects_invalid_likelihood(likelihood: str):
    with pytest.raises(ValidationError, match="literal_error"):
        DifferentialDiagnosis(
            condition="migraine",
            likelihood=likelihood,
            reasoning="Symptoms are compatible with migraine.",
            missing_information=["neurologic exam"],
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
                referrals=["Primary care"],
                follow_up="",
                red_flags=["worsening pain"],
            ),
            "follow_up",
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
                condition="viral syndrome",
                likelihood="low",
                reasoning="",
                missing_information=["temperature"],
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
                    referrals=[],
                    follow_up="Monitor symptoms over 24 hours.",
                    red_flags=[],
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
    assert bundle.care_plan.follow_up == "Immediate emergency evaluation is recommended today."


def test_final_consultation_bundle_round_trips_from_json():
    bundle = FinalConsultationBundle.model_validate_json(
        FIXTURE_PATH.read_text(encoding="utf-8")
    )

    dumped = bundle.model_dump(mode="json")

    assert dumped["case"]["patient_id"] == "P-1024"
    assert dumped["soap_note"]["assessment"] == "Symptoms are concerning for acute coronary syndrome."
    assert dumped["differentials"][1]["condition"] == "pulmonary embolism"


def test_consultation_case_schema_exposes_example_json():
    schema = ConsultationCase.model_json_schema()

    assert "example" in schema
    assert schema["example"]["chief_complaint"] == "Chest pain"
