from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from src.contracts.consultation import CarePlan, ConsultationCase, DifferentialDiagnosis, SoapNote
from src.tools.soap_note_tool import (
    OBJECTIVE_FALLBACK,
    SoapNoteGenerationError,
    SoapNoteResponse,
    build_soap_note_input,
    generate_soap,
)


def make_case() -> ConsultationCase:
    return ConsultationCase(
        patient_id="P-6001",
        chief_complaint="Chest pain",
        symptoms=["chest pain", "shortness of breath"],
        duration="2 hours",
        severity="severe",
        history=["hypertension"],
        risk_factors=["smoking"],
        transcript="Patient reports chest pain and shortness of breath for two hours.",
    )


def make_differentials() -> list[DifferentialDiagnosis]:
    return [
        DifferentialDiagnosis(
            condition_name="acute coronary syndrome",
            likelihood="high",
            reasoning="Chest pain and shortness of breath make acute coronary syndrome an important consideration, but confirmatory testing is not available.",
            supporting_findings=["chest pain", "shortness of breath"],
            conflicting_findings=["No ECG or troponin results are available."],
            missing_information=["ECG", "troponin"],
            recommended_tests=["ECG", "troponin"],
            urgency="urgent in-person assessment should be considered because symptoms may reflect a time-sensitive condition",
        )
    ]


def make_care_plan() -> CarePlan:
    return CarePlan(
        suggested_tests=["ECG", "troponin"],
        suggested_referrals=["Emergency department"],
        follow_up=["Arrange urgent same-day assessment."],
        red_flags=["worsening chest pain", "fainting"],
        patient_advice=["Seek urgent review if symptoms worsen."],
        rationale="The plan prioritizes urgent evaluation for potentially serious cardiopulmonary causes.",
    )


def make_soap_note() -> SoapNote:
    return SoapNote(
        subjective="Patient reports chest pain and shortness of breath for two hours.",
        objective="Blood pressure was 160/90.",
        assessment="Symptoms are concerning for serious cardiopulmonary causes, including acute coronary syndrome.",
        plan="Urgent in-person evaluation and initial cardiac testing are recommended.",
    )


def test_build_soap_note_input_includes_case_differentials_plan_and_objective_status():
    payload = build_soap_note_input(make_case(), make_differentials(), make_care_plan())

    assert "CONSULTATION CASE" in payload
    assert '"chief_complaint": "Chest pain"' in payload
    assert "DIFFERENTIAL DIAGNOSIS LIST" in payload
    assert '"condition_name": "acute coronary syndrome"' in payload
    assert "CARE PLAN" in payload
    assert '"suggested_tests": [' in payload
    assert "OBJECTIVE DATA STATUS" in payload
    assert OBJECTIVE_FALLBACK in payload


def test_build_soap_note_input_handles_missing_differentials():
    payload = build_soap_note_input(make_case(), [], make_care_plan())

    assert "No differential diagnoses were provided." in payload


def test_generate_soap_returns_typed_contract_and_forces_safe_objective_fallback():
    fake_response = Mock()
    fake_response.output_parsed = SoapNoteResponse(soap_note=make_soap_note())

    with patch(
        "src.tools.soap_note_tool.load_soap_note_prompt",
        return_value="prompt",
    ), patch("src.tools.soap_note_tool.OpenAI") as mock_openai:
        mock_client = Mock()
        mock_client.responses.parse.return_value = fake_response
        mock_openai.return_value = mock_client

        result = generate_soap(make_case(), make_differentials(), make_care_plan())

    assert result.subjective == make_soap_note().subjective
    assert result.objective == OBJECTIVE_FALLBACK
    assert result.assessment == make_soap_note().assessment
    mock_client.responses.parse.assert_called_once()
    call = mock_client.responses.parse.call_args.kwargs
    assert call["model"] == "gpt-5-nano"
    assert call["input"][0] == {"role": "system", "content": "prompt"}
    assert "OBJECTIVE DATA STATUS" in call["input"][1]["content"]
    assert call["text_format"] is SoapNoteResponse


def test_generate_soap_wraps_validation_failure():
    try:
        SoapNoteResponse.model_validate(
            {
                "soap_note": {
                    "subjective": "",
                    "objective": "",
                    "assessment": "",
                    "plan": "",
                }
            }
        )
    except ValidationError as exc:
        validation_error = exc
    else:
        raise AssertionError("Expected invalid SOAP note payload to fail")

    with patch(
        "src.tools.soap_note_tool.load_soap_note_prompt",
        return_value="prompt",
    ), patch("src.tools.soap_note_tool.OpenAI") as mock_openai:
        mock_client = Mock()
        mock_client.responses.parse.side_effect = validation_error
        mock_openai.return_value = mock_client

        with pytest.raises(
            SoapNoteGenerationError,
            match="Model output failed SOAP note validation",
        ):
            generate_soap(make_case(), make_differentials(), make_care_plan())


def test_generate_soap_raises_when_no_parsed_output():
    fake_response = Mock()
    fake_response.output_parsed = None

    with patch(
        "src.tools.soap_note_tool.load_soap_note_prompt",
        return_value="prompt",
    ), patch("src.tools.soap_note_tool.OpenAI") as mock_openai:
        mock_client = Mock()
        mock_client.responses.parse.return_value = fake_response
        mock_openai.return_value = mock_client

        with pytest.raises(
            SoapNoteGenerationError,
            match="Model returned no parsed SOAP note",
        ):
            generate_soap(make_case(), make_differentials(), make_care_plan())
