from __future__ import annotations

from pathlib import Path

from openai import OpenAI
from pydantic import ValidationError

from src.contracts.consultation import ConsultationCase


class CaseExtractionError(Exception):
    """Raised when structured case extraction fails."""


def _prompt_path() -> Path:
    return Path(__file__).resolve().parents[1] / "prompts" / "case_extraction_system_prompt.md"


def load_case_extraction_prompt() -> str:
    path = _prompt_path()
    if not path.exists():
        raise CaseExtractionError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def build_case_extraction_input(
    transcript_text: str,
    doctor_notes: str | None = None,
) -> str:
    transcript = transcript_text.strip()
    if not transcript:
        raise ValueError("transcript_text must not be empty")

    notes = (doctor_notes or "").strip()

    return f"""
DOCTOR NOTES
------------
{notes if notes else "No doctor notes provided."}

CONSULTATION TRANSCRIPT
-----------------------
{transcript}
""".strip()


def extract_consultation_case(
    transcript_text: str,
    doctor_notes: str | None = None,
    model: str = "gpt-5-nano",
) -> ConsultationCase:
    """
    Extract a structured ConsultationCase from consultation transcript text
    and optional doctor notes.

    Returns a validated ConsultationCase object.
    """
    transcript = transcript_text.strip()
    if not transcript:
        raise ValueError("transcript_text must not be empty")

    system_prompt = load_case_extraction_prompt()
    user_input = build_case_extraction_input(
        transcript_text=transcript,
        doctor_notes=doctor_notes,
    )

    client = OpenAI()

    try:
        response = client.responses.parse(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            text_format=ConsultationCase,
        )
        parsed = response.output_parsed

        if parsed is None:
            raise CaseExtractionError("Model returned no parsed ConsultationCase")

        # Keep the returned contract self-contained even if the model omits
        # or alters the raw transcript field.
        return parsed.model_copy(update={"transcript": transcript})
    except ValidationError as exc:
        raise CaseExtractionError(
            "Model output failed ConsultationCase validation"
        ) from exc
    except CaseExtractionError:
        raise
    except Exception as exc:
        raise CaseExtractionError("Case extraction failed") from exc
