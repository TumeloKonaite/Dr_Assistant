from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from src.contracts.consultation import ConsultationCase
from src.tools.case_extraction_tool import (
    CaseExtractionError,
    build_case_extraction_input,
    extract_consultation_case,
)


def make_fake_case() -> ConsultationCase:
    return ConsultationCase(
        patient_id="P-2001",
        chief_complaint="Headache",
        symptoms=["headache", "fatigue"],
        duration="2 days",
        severity="moderate",
        medications=["ibuprofen"],
        allergies=["penicillin"],
        history=["previous migraines"],
        risk_factors=["stress"],
        transcript="placeholder transcript",
    )


def test_build_case_extraction_input_requires_transcript():
    with pytest.raises(ValueError, match="transcript_text must not be empty"):
        build_case_extraction_input(transcript_text="", doctor_notes="some notes")


def test_build_case_extraction_input_includes_default_notes_message():
    payload = build_case_extraction_input(
        transcript_text="Patient reports chest pain.",
        doctor_notes=None,
    )

    assert "No doctor notes provided." in payload
    assert "Patient reports chest pain." in payload


def test_extract_consultation_case_returns_valid_contract():
    transcript = "I have had a headache for two days and I feel tired."
    fake_case = make_fake_case()

    fake_response = Mock()
    fake_response.output_parsed = fake_case

    with patch(
        "src.tools.case_extraction_tool.load_case_extraction_prompt",
        return_value="prompt",
    ), patch("src.tools.case_extraction_tool.OpenAI") as mock_openai:
        mock_client = Mock()
        mock_client.responses.parse.return_value = fake_response
        mock_openai.return_value = mock_client

        result = extract_consultation_case(
            transcript_text=transcript,
            doctor_notes="Patient looks uncomfortable.",
        )

    assert isinstance(result, ConsultationCase)
    assert result.chief_complaint == "Headache"
    assert result.transcript == transcript
    assert result.history == ["previous migraines"]
    mock_client.responses.parse.assert_called_once_with(
        model="gpt-5-nano",
        input=[
            {"role": "system", "content": "prompt"},
            {
                "role": "user",
                "content": (
                    "DOCTOR NOTES\n"
                    "------------\n"
                    "Patient looks uncomfortable.\n\n"
                    "CONSULTATION TRANSCRIPT\n"
                    "-----------------------\n"
                    "I have had a headache for two days and I feel tired."
                ),
            },
        ],
        text_format=ConsultationCase,
    )


def test_extract_consultation_case_supports_missing_doctor_notes():
    transcript = "I have had chest pain since yesterday."
    fake_case = ConsultationCase(
        chief_complaint="Chest pain",
        symptoms=["chest pain"],
        duration="since yesterday",
        severity=None,
        medications=[],
        allergies=[],
        history=[],
        risk_factors=[],
        transcript="placeholder transcript",
    )

    fake_response = Mock()
    fake_response.output_parsed = fake_case

    with patch(
        "src.tools.case_extraction_tool.load_case_extraction_prompt",
        return_value="prompt",
    ), patch("src.tools.case_extraction_tool.OpenAI") as mock_openai:
        mock_client = Mock()
        mock_client.responses.parse.return_value = fake_response
        mock_openai.return_value = mock_client

        result = extract_consultation_case(transcript_text=transcript)

    assert result.transcript == transcript
    assert result.chief_complaint == "Chest pain"


def test_extract_consultation_case_wraps_validation_failure():
    try:
        ConsultationCase.model_validate(
            {
                "chief_complaint": "",
                "transcript": "",
            }
        )
    except ValidationError as exc:
        validation_error = exc
    else:
        raise AssertionError("Expected invalid ConsultationCase payload to fail")

    with patch(
        "src.tools.case_extraction_tool.load_case_extraction_prompt",
        return_value="prompt",
    ), patch("src.tools.case_extraction_tool.OpenAI") as mock_openai:
        mock_client = Mock()
        mock_client.responses.parse.side_effect = validation_error
        mock_openai.return_value = mock_client

        with pytest.raises(
            CaseExtractionError,
            match="Model output failed ConsultationCase validation",
        ):
            extract_consultation_case(
                transcript_text="Patient reports dizziness.",
                doctor_notes="",
            )


def test_extract_consultation_case_wraps_api_failure():
    with patch(
        "src.tools.case_extraction_tool.load_case_extraction_prompt",
        return_value="prompt",
    ), patch("src.tools.case_extraction_tool.OpenAI") as mock_openai:
        mock_client = Mock()
        mock_client.responses.parse.side_effect = Exception("API failure")
        mock_openai.return_value = mock_client

        with pytest.raises(CaseExtractionError, match="Case extraction failed"):
            extract_consultation_case(
                transcript_text="Patient reports dizziness.",
                doctor_notes="",
            )


def test_extract_consultation_case_raises_when_no_parsed_output():
    fake_response = Mock()
    fake_response.output_parsed = None

    with patch(
        "src.tools.case_extraction_tool.load_case_extraction_prompt",
        return_value="prompt",
    ), patch("src.tools.case_extraction_tool.OpenAI") as mock_openai:
        mock_client = Mock()
        mock_client.responses.parse.return_value = fake_response
        mock_openai.return_value = mock_client

        with pytest.raises(
            CaseExtractionError,
            match="Model returned no parsed ConsultationCase",
        ):
            extract_consultation_case(
                transcript_text="Patient reports dizziness.",
                doctor_notes="",
            )
