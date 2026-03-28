from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from src.contracts.consultation import (
    ConsultationCase,
    DifferentialDiagnosis,
    RetrievedCondition,
)
from src.tools.differential_generation_tool import (
    DifferentialGenerationError,
    DifferentialGenerationResponse,
    build_differential_generation_input,
    generate_differentials,
)


def make_case() -> ConsultationCase:
    return ConsultationCase(
        patient_id="P-3001",
        chief_complaint="Cough",
        symptoms=["cough", "fever", "shortness of breath"],
        duration="3 days",
        severity="moderate",
        history=["asthma"],
        transcript="Patient reports cough, fever, and shortness of breath for three days.",
    )


def make_retrieved() -> list[RetrievedCondition]:
    return [
        RetrievedCondition(
            name="pneumonia",
            description="Infection of the lung parenchyma.",
            matched_symptoms=["cough", "fever", "shortness of breath"],
            score=0.92,
        ),
        RetrievedCondition(
            name="viral upper respiratory infection",
            description="Common viral respiratory illness.",
            matched_symptoms=["cough", "fever"],
            score=0.74,
        ),
    ]


def make_differentials() -> list[DifferentialDiagnosis]:
    return [
        DifferentialDiagnosis(
            condition_name="pneumonia",
            likelihood="high",
            reasoning="Fever, cough, and dyspnea make pneumonia a strong consideration, although the exam and imaging are not yet available.",
            supporting_findings=["cough", "fever", "shortness of breath"],
            conflicting_findings=["No lung exam findings or imaging are available."],
            missing_information=["oxygen saturation", "chest exam findings"],
            recommended_tests=["chest X-ray", "pulse oximetry"],
            urgency="urgent review should be considered if dyspnea worsens or oxygenation is impaired",
        )
    ]


def test_build_differential_generation_input_includes_case_and_retrieval():
    payload = build_differential_generation_input(make_case(), make_retrieved())

    assert "CONSULTATION CASE" in payload
    assert '"chief_complaint": "Cough"' in payload
    assert "RETRIEVED CANDIDATE CONDITIONS" in payload
    assert '"name": "pneumonia"' in payload


def test_build_differential_generation_input_handles_empty_retrieval():
    payload = build_differential_generation_input(make_case(), [])

    assert "No retrieved candidate conditions were provided." in payload


def test_generate_differentials_returns_typed_list():
    fake_response = Mock()
    fake_response.output_parsed = DifferentialGenerationResponse(
        differentials=make_differentials()
    )

    with patch(
        "src.tools.differential_generation_tool.load_differential_generation_prompt",
        return_value="prompt",
    ), patch("src.tools.differential_generation_tool.OpenAI") as mock_openai:
        mock_client = Mock()
        mock_client.responses.parse.return_value = fake_response
        mock_openai.return_value = mock_client

        result = generate_differentials(make_case(), make_retrieved())

    assert result == make_differentials()
    mock_client.responses.parse.assert_called_once()
    call = mock_client.responses.parse.call_args.kwargs
    assert call["model"] == "gpt-5-nano"
    assert call["input"][0] == {"role": "system", "content": "prompt"}
    assert "CONSULTATION CASE" in call["input"][1]["content"]
    assert "RETRIEVED CANDIDATE CONDITIONS" in call["input"][1]["content"]
    assert call["text_format"] is DifferentialGenerationResponse


def test_generate_differentials_wraps_validation_failure():
    try:
        DifferentialGenerationResponse.model_validate(
            {
                "differentials": [
                    {
                        "condition_name": "",
                        "likelihood": "high",
                        "reasoning": "text",
                    }
                ]
            }
        )
    except ValidationError as exc:
        validation_error = exc
    else:
        raise AssertionError("Expected invalid differential response payload to fail")

    with patch(
        "src.tools.differential_generation_tool.load_differential_generation_prompt",
        return_value="prompt",
    ), patch("src.tools.differential_generation_tool.OpenAI") as mock_openai:
        mock_client = Mock()
        mock_client.responses.parse.side_effect = validation_error
        mock_openai.return_value = mock_client

        with pytest.raises(
            DifferentialGenerationError,
            match="Model output failed differential diagnosis validation",
        ):
            generate_differentials(make_case(), make_retrieved())


def test_generate_differentials_raises_when_no_parsed_output():
    fake_response = Mock()
    fake_response.output_parsed = None

    with patch(
        "src.tools.differential_generation_tool.load_differential_generation_prompt",
        return_value="prompt",
    ), patch("src.tools.differential_generation_tool.OpenAI") as mock_openai:
        mock_client = Mock()
        mock_client.responses.parse.return_value = fake_response
        mock_openai.return_value = mock_client

        with pytest.raises(
            DifferentialGenerationError,
            match="Model returned no parsed differential diagnoses",
        ):
            generate_differentials(make_case(), make_retrieved())
