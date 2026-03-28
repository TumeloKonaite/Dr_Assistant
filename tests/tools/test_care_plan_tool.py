from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from src.contracts.consultation import CarePlan, ConsultationCase, DifferentialDiagnosis
from src.tools.care_plan_tool import (
    CarePlanGenerationError,
    CarePlanResponse,
    build_care_plan_input,
    generate_care_plan,
)


def make_case() -> ConsultationCase:
    return ConsultationCase(
        patient_id="P-4001",
        chief_complaint="Chest pain",
        symptoms=["chest pain", "shortness of breath", "dizziness"],
        duration="2 hours",
        severity="severe",
        risk_factors=["smoking"],
        transcript="Patient reports chest pain, shortness of breath, and dizziness for two hours.",
    )


def make_differentials() -> list[DifferentialDiagnosis]:
    return [
        DifferentialDiagnosis(
            condition_name="acute coronary syndrome",
            likelihood="high",
            reasoning="Chest pain, dyspnea, and dizziness make acute coronary syndrome an important consideration, but confirmatory testing is not available yet.",
            supporting_findings=["chest pain", "shortness of breath", "dizziness"],
            conflicting_findings=["No ECG or troponin data are available."],
            missing_information=["ECG findings", "troponin", "pain radiation"],
            recommended_tests=["ECG", "troponin"],
            urgency="urgent same-day assessment should be considered because the symptom pattern may reflect a time-sensitive cardiopulmonary condition",
        )
    ]


def make_care_plan() -> CarePlan:
    return CarePlan(
        suggested_tests=["ECG", "troponin", "chest X-ray"],
        suggested_referrals=["Emergency department", "Cardiology"],
        follow_up=[
            "Arrange urgent same-day in-person assessment.",
            "Reassess after initial testing to refine the differential.",
        ],
        red_flags=["worsening chest pain", "syncope", "increasing shortness of breath"],
        patient_advice=[
            "Seek urgent medical review if symptoms intensify or new concerning symptoms develop."
        ],
        rationale="The plan prioritizes urgent evaluation for serious cardiopulmonary causes while preserving diagnostic uncertainty.",
    )


def test_build_care_plan_input_includes_case_and_differentials():
    payload = build_care_plan_input(make_case(), make_differentials())

    assert "CONSULTATION CASE" in payload
    assert '"chief_complaint": "Chest pain"' in payload
    assert "DIFFERENTIAL DIAGNOSIS LIST" in payload
    assert '"condition_name": "acute coronary syndrome"' in payload


def test_build_care_plan_input_handles_missing_differentials():
    payload = build_care_plan_input(make_case(), [])

    assert "No differential diagnoses were provided." in payload


def test_generate_care_plan_returns_typed_contract():
    fake_response = Mock()
    fake_response.output_parsed = CarePlanResponse(care_plan=make_care_plan())

    with patch(
        "src.tools.care_plan_tool.load_care_plan_prompt",
        return_value="prompt",
    ), patch("src.tools.care_plan_tool.OpenAI") as mock_openai:
        mock_client = Mock()
        mock_client.responses.parse.return_value = fake_response
        mock_openai.return_value = mock_client

        result = generate_care_plan(make_case(), make_differentials())

    assert result == make_care_plan()
    mock_client.responses.parse.assert_called_once()
    call = mock_client.responses.parse.call_args.kwargs
    assert call["model"] == "gpt-5-nano"
    assert call["input"][0] == {"role": "system", "content": "prompt"}
    assert "DIFFERENTIAL DIAGNOSIS LIST" in call["input"][1]["content"]
    assert call["text_format"] is CarePlanResponse


def test_generate_care_plan_wraps_validation_failure():
    try:
        CarePlanResponse.model_validate(
            {
                "care_plan": {
                    "suggested_tests": [],
                    "suggested_referrals": [],
                    "follow_up": [],
                    "red_flags": [],
                    "patient_advice": [],
                    "rationale": "",
                }
            }
        )
    except ValidationError as exc:
        validation_error = exc
    else:
        raise AssertionError("Expected invalid care plan payload to fail")

    with patch(
        "src.tools.care_plan_tool.load_care_plan_prompt",
        return_value="prompt",
    ), patch("src.tools.care_plan_tool.OpenAI") as mock_openai:
        mock_client = Mock()
        mock_client.responses.parse.side_effect = validation_error
        mock_openai.return_value = mock_client

        with pytest.raises(
            CarePlanGenerationError,
            match="Model output failed care plan validation",
        ):
            generate_care_plan(make_case(), make_differentials())


def test_generate_care_plan_raises_when_no_parsed_output():
    fake_response = Mock()
    fake_response.output_parsed = None

    with patch(
        "src.tools.care_plan_tool.load_care_plan_prompt",
        return_value="prompt",
    ), patch("src.tools.care_plan_tool.OpenAI") as mock_openai:
        mock_client = Mock()
        mock_client.responses.parse.return_value = fake_response
        mock_openai.return_value = mock_client

        with pytest.raises(
            CarePlanGenerationError,
            match="Model returned no parsed care plan",
        ):
            generate_care_plan(make_case(), make_differentials())
