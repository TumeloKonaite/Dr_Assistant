from __future__ import annotations

import json
from pathlib import Path

from openai import OpenAI
from pydantic import ValidationError

from src.contracts.consultation import (
    CarePlan,
    ConsultationCase,
    ContractModel,
    DifferentialDiagnosis,
)


class CarePlanGenerationError(Exception):
    """Raised when care plan generation fails."""


class CarePlanResponse(ContractModel):
    care_plan: CarePlan


def _prompt_path() -> Path:
    return Path(__file__).resolve().parents[1] / "prompts" / "care_plan_system_prompt.md"


def load_care_plan_prompt() -> str:
    path = _prompt_path()
    if not path.exists():
        raise CarePlanGenerationError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def build_care_plan_input(
    case: ConsultationCase,
    differentials: list[DifferentialDiagnosis],
) -> str:
    differential_payload: list[dict] | str
    if differentials:
        differential_payload = [item.model_dump(mode="json") for item in differentials]
    else:
        differential_payload = "No differential diagnoses were provided."

    return "\n".join(
        [
            "CONSULTATION CASE",
            "-----------------",
            json.dumps(case.model_dump(mode="json"), indent=2),
            "",
            "DIFFERENTIAL DIAGNOSIS LIST",
            "---------------------------",
            json.dumps(differential_payload, indent=2)
            if isinstance(differential_payload, list)
            else differential_payload,
        ]
    )


def generate_care_plan(
    case: ConsultationCase,
    differentials: list[DifferentialDiagnosis],
    model: str = "gpt-5-nano",
) -> CarePlan:
    system_prompt = load_care_plan_prompt()
    user_input = build_care_plan_input(case=case, differentials=differentials)
    client = OpenAI()

    try:
        response = client.responses.parse(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            text_format=CarePlanResponse,
        )
        parsed = response.output_parsed

        if parsed is None:
            raise CarePlanGenerationError("Model returned no parsed care plan")

        return parsed.care_plan
    except ValidationError as exc:
        raise CarePlanGenerationError(
            "Model output failed care plan validation"
        ) from exc
    except CarePlanGenerationError:
        raise
    except Exception as exc:
        raise CarePlanGenerationError("Care plan generation failed") from exc
