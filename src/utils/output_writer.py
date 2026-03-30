from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from src.contracts.consultation import PatientSummary, SoapNote


def ensure_output_dir(path: str | Path) -> Path:
    output_dir = Path(path)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def write_text_output(path: str | Path, content: str) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def write_json_output(path: str | Path, payload: Any) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(payload, BaseModel):
        data = payload.model_dump(mode="json")
    elif isinstance(payload, list):
        data = [
            item.model_dump(mode="json") if isinstance(item, BaseModel) else item
            for item in payload
        ]
    else:
        data = payload

    output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return output_path


def render_soap_note(soap_note: SoapNote) -> str:
    return "\n".join(
        [
            "# SOAP Note",
            "",
            "## Subjective",
            soap_note.subjective,
            "",
            "## Objective",
            soap_note.objective,
            "",
            "## Assessment",
            soap_note.assessment,
            "",
            "## Plan",
            soap_note.plan,
        ]
    )


def render_patient_summary(summary: PatientSummary) -> str:
    def render_list(items: list[str]) -> str:
        if not items:
            return "None documented."
        return "\n".join(f"- {item}" for item in items)

    return "\n".join(
        [
            "# Patient Summary",
            "",
            "## What Was Discussed",
            summary.what_was_discussed,
            "",
            "## What the Doctor May Check Next",
            render_list(summary.what_the_doctor_may_check_next),
            "",
            "## What You Should Do Next",
            render_list(summary.what_you_should_do_next),
            "",
            "## When to Get Urgent Help",
            render_list(summary.when_to_get_urgent_help),
        ]
    )
