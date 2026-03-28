from __future__ import annotations

import json
from pathlib import Path

from openai import OpenAI
from pydantic import ValidationError

from src.contracts.consultation import (
    ConsultationCase,
    ContractModel,
    DifferentialDiagnosis,
    RetrievedCondition,
)


class DifferentialGenerationError(Exception):
    """Raised when differential generation fails."""


class DifferentialGenerationResponse(ContractModel):
    differentials: list[DifferentialDiagnosis]


def _prompt_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "prompts"
        / "differential_generation_system_prompt.md"
    )


def load_differential_generation_prompt() -> str:
    path = _prompt_path()
    if not path.exists():
        raise DifferentialGenerationError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def build_differential_generation_input(
    case: ConsultationCase,
    retrieved: list[RetrievedCondition],
) -> str:
    retrieved_payload: list[dict] | str
    if retrieved:
        retrieved_payload = [item.model_dump(mode="json") for item in retrieved]
    else:
        retrieved_payload = "No retrieved candidate conditions were provided."

    return "\n".join(
        [
            "CONSULTATION CASE",
            "-----------------",
            json.dumps(case.model_dump(mode="json"), indent=2),
            "",
            "RETRIEVED CANDIDATE CONDITIONS",
            "------------------------------",
            json.dumps(retrieved_payload, indent=2)
            if isinstance(retrieved_payload, list)
            else retrieved_payload,
        ]
    )


def generate_differentials(
    case: ConsultationCase,
    retrieved: list[RetrievedCondition],
    model: str = "gpt-5-nano",
) -> list[DifferentialDiagnosis]:
    system_prompt = load_differential_generation_prompt()
    user_input = build_differential_generation_input(case=case, retrieved=retrieved)
    client = OpenAI()

    try:
        response = client.responses.parse(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            text_format=DifferentialGenerationResponse,
        )
        parsed = response.output_parsed

        if parsed is None:
            raise DifferentialGenerationError(
                "Model returned no parsed differential diagnoses"
            )

        return parsed.differentials
    except ValidationError as exc:
        raise DifferentialGenerationError(
            "Model output failed differential diagnosis validation"
        ) from exc
    except DifferentialGenerationError:
        raise
    except Exception as exc:
        raise DifferentialGenerationError("Differential generation failed") from exc
