from __future__ import annotations

import json
from pathlib import Path

from src.contracts.consultation import DocumentationBundle


def _render_list(items: list[str], empty_message: str = "None documented.") -> str:
    if not items:
        return empty_message
    return "\n".join(f"- {item}" for item in items)


def bundle_to_json(bundle: DocumentationBundle) -> str:
    return json.dumps(bundle.model_dump(mode="json"), indent=2)


def bundle_to_markdown(bundle: DocumentationBundle) -> str:
    soap_note = bundle.soap_note
    patient_summary = bundle.patient_summary

    sections = [
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
        "",
        "# Patient Summary",
        "",
        "## What Was Discussed",
        patient_summary.what_was_discussed,
        "",
        "## What the Doctor May Check Next",
        _render_list(patient_summary.what_the_doctor_may_check_next),
        "",
        "## What You Should Do Next",
        _render_list(patient_summary.what_you_should_do_next),
        "",
        "## When to Get Urgent Help",
        _render_list(patient_summary.when_to_get_urgent_help),
    ]

    return "\n".join(sections)


def write_bundle_json(bundle: DocumentationBundle, path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(bundle_to_json(bundle), encoding="utf-8")


def write_bundle_markdown(bundle: DocumentationBundle, path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(bundle_to_markdown(bundle), encoding="utf-8")
