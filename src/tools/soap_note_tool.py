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
    SoapNote,
)


OBJECTIVE_FALLBACK = (
    "No vital signs, examination findings, laboratory results, or imaging results "
    "were available in the source materials."
)


class SoapNoteGenerationError(Exception):
    """Raised when SOAP note generation fails."""


class SoapNoteResponse(ContractModel):
    soap_note: SoapNote


def _prompt_path() -> Path:
    return Path(__file__).resolve().parents[1] / "prompts" / "soap_note_system_prompt.md"


def load_soap_note_prompt() -> str:
    path = _prompt_path()
    if not path.exists():
        raise SoapNoteGenerationError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def build_soap_note_input(
    case: ConsultationCase,
    differentials: list[DifferentialDiagnosis],
    plan: CarePlan,
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
            "",
            "CARE PLAN",
            "---------",
            json.dumps(plan.model_dump(mode="json"), indent=2),
            "",
            "OBJECTIVE DATA STATUS",
            "---------------------",
            OBJECTIVE_FALLBACK,
        ]
    )


def generate_soap(
    case: ConsultationCase,
    differentials: list[DifferentialDiagnosis],
    plan: CarePlan,
    model: str = "gpt-5-nano",
) -> SoapNote:
    system_prompt = load_soap_note_prompt()
    user_input = build_soap_note_input(case=case, differentials=differentials, plan=plan)
    client = OpenAI()

    try:
        response = client.responses.parse(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            text_format=SoapNoteResponse,
        )
        parsed = response.output_parsed

        if parsed is None:
            raise SoapNoteGenerationError("Model returned no parsed SOAP note")

        # The current structured inputs do not include reliable objective fields.
        # Force a safe, explicit fallback instead of trusting inferred findings.
        return parsed.soap_note.model_copy(update={"objective": OBJECTIVE_FALLBACK})
    except ValidationError as exc:
        raise SoapNoteGenerationError("Model output failed SOAP note validation") from exc
    except SoapNoteGenerationError:
        raise
    except Exception as exc:
        raise SoapNoteGenerationError("SOAP note generation failed") from exc
