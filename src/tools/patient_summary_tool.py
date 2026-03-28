from __future__ import annotations

import json
from pathlib import Path

from openai import OpenAI
from pydantic import ValidationError

from src.contracts.consultation import (
    CarePlan,
    ConsultationCase,
    ContractModel,
    PatientSummary,
)


class PatientSummaryGenerationError(Exception):
    """Raised when patient summary generation fails."""


class PatientSummaryResponse(ContractModel):
    patient_summary: PatientSummary


def _prompt_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "prompts"
        / "patient_summary_system_prompt.md"
    )


def load_patient_summary_prompt() -> str:
    path = _prompt_path()
    if not path.exists():
        raise PatientSummaryGenerationError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def build_patient_summary_input(
    case: ConsultationCase,
    plan: CarePlan,
) -> str:
    return "\n".join(
        [
            "CONSULTATION CASE",
            "-----------------",
            json.dumps(case.model_dump(mode="json"), indent=2),
            "",
            "CARE PLAN",
            "---------",
            json.dumps(plan.model_dump(mode="json"), indent=2),
        ]
    )


def generate_patient_summary(
    case: ConsultationCase,
    plan: CarePlan,
    model: str = "gpt-5-nano",
) -> PatientSummary:
    system_prompt = load_patient_summary_prompt()
    user_input = build_patient_summary_input(case=case, plan=plan)
    client = OpenAI()

    try:
        response = client.responses.parse(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            text_format=PatientSummaryResponse,
        )
        parsed = response.output_parsed

        if parsed is None:
            raise PatientSummaryGenerationError(
                "Model returned no parsed patient summary"
            )

        return parsed.patient_summary
    except ValidationError as exc:
        raise PatientSummaryGenerationError(
            "Model output failed patient summary validation"
        ) from exc
    except PatientSummaryGenerationError:
        raise
    except Exception as exc:
        raise PatientSummaryGenerationError("Patient summary generation failed") from exc
