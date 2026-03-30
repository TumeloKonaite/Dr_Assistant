from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from src.contracts.consultation import CarePlan, ConsultationCase, PatientSummary
from src.tools.patient_summary_tool import (
    PatientSummaryGenerationError,
    PatientSummaryResponse,
    build_patient_summary_input,
    generate_patient_summary,
)


def make_case() -> ConsultationCase:
    return ConsultationCase(
        patient_id="P-6002",
        chief_complaint="Abdominal pain",
        symptoms=["abdominal pain", "nausea"],
        duration="1 day",
        severity="moderate",
        transcript="Patient reports abdominal pain and nausea since yesterday.",
    )


def make_care_plan() -> CarePlan:
    return CarePlan(
        suggested_tests=["CBC"],
        suggested_referrals=["Primary care"],
        follow_up=["Follow up within 48 hours if symptoms persist."],
        red_flags=["vomiting blood", "black stools"],
        patient_advice=["Drink fluids and seek urgent help if bleeding occurs."],
        rationale="The plan focuses on reassessment and escalation if bleeding or worsening symptoms develop.",
    )


def make_patient_summary() -> PatientSummary:
    return PatientSummary(
        what_was_discussed="You reported abdominal pain and nausea that started yesterday.",
        what_the_doctor_may_check_next=["A blood test if symptoms continue."],
        what_you_should_do_next=["Follow up within 48 hours if symptoms persist."],
        when_to_get_urgent_help=["Get urgent help if you vomit blood or have black stools."],
    )


def test_build_patient_summary_input_includes_case_and_plan():
    payload = build_patient_summary_input(make_case(), make_care_plan())

    assert "CONSULTATION CASE" in payload
    assert '"chief_complaint": "Abdominal pain"' in payload
    assert "CARE PLAN" in payload
    assert '"suggested_tests": [' in payload


def test_build_patient_summary_input_includes_safety_context_when_provided():
    payload = build_patient_summary_input(
        make_case(),
        make_care_plan(),
        safety_context="Urgent red flags detected: Possible gastrointestinal bleeding.",
    )

    assert "SAFETY CONTEXT" in payload
    assert "Possible gastrointestinal bleeding" in payload


def test_generate_patient_summary_returns_typed_contract():
    fake_response = Mock()
    fake_response.output_parsed = PatientSummaryResponse(
        patient_summary=make_patient_summary()
    )

    with patch(
        "src.tools.patient_summary_tool.load_patient_summary_prompt",
        return_value="prompt",
    ), patch("src.tools.patient_summary_tool.OpenAI") as mock_openai:
        mock_client = Mock()
        mock_client.responses.parse.return_value = fake_response
        mock_openai.return_value = mock_client

        result = generate_patient_summary(make_case(), make_care_plan())

    assert result == make_patient_summary()
    mock_client.responses.parse.assert_called_once()
    call = mock_client.responses.parse.call_args.kwargs
    assert call["model"] == "gpt-5-nano"
    assert call["input"][0] == {"role": "system", "content": "prompt"}
    assert "CONSULTATION CASE" in call["input"][1]["content"]
    assert call["text_format"] is PatientSummaryResponse


def test_generate_patient_summary_wraps_validation_failure():
    try:
        PatientSummaryResponse.model_validate(
            {
                "patient_summary": {
                    "what_was_discussed": "",
                    "what_the_doctor_may_check_next": [],
                    "what_you_should_do_next": [],
                    "when_to_get_urgent_help": [],
                }
            }
        )
    except ValidationError as exc:
        validation_error = exc
    else:
        raise AssertionError("Expected invalid patient summary payload to fail")

    with patch(
        "src.tools.patient_summary_tool.load_patient_summary_prompt",
        return_value="prompt",
    ), patch("src.tools.patient_summary_tool.OpenAI") as mock_openai:
        mock_client = Mock()
        mock_client.responses.parse.side_effect = validation_error
        mock_openai.return_value = mock_client

        with pytest.raises(
            PatientSummaryGenerationError,
            match="Model output failed patient summary validation",
        ):
            generate_patient_summary(make_case(), make_care_plan())


def test_generate_patient_summary_raises_when_no_parsed_output():
    fake_response = Mock()
    fake_response.output_parsed = None

    with patch(
        "src.tools.patient_summary_tool.load_patient_summary_prompt",
        return_value="prompt",
    ), patch("src.tools.patient_summary_tool.OpenAI") as mock_openai:
        mock_client = Mock()
        mock_client.responses.parse.return_value = fake_response
        mock_openai.return_value = mock_client

        with pytest.raises(
            PatientSummaryGenerationError,
            match="Model returned no parsed patient summary",
        ):
            generate_patient_summary(make_case(), make_care_plan())
