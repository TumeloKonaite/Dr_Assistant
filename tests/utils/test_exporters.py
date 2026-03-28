import json
from pathlib import Path
from uuid import uuid4

from src.contracts.consultation import DocumentationBundle, PatientSummary, SoapNote
from src.utils.exporters import (
    bundle_to_json,
    bundle_to_markdown,
    write_bundle_json,
    write_bundle_markdown,
)


def make_bundle() -> DocumentationBundle:
    return DocumentationBundle(
        soap_note=SoapNote(
            subjective="Patient reports abdominal pain and nausea since yesterday.",
            objective="No vital signs, examination findings, laboratory results, or imaging results were available in the source materials.",
            assessment="Symptoms warrant follow-up evaluation while preserving diagnostic uncertainty.",
            plan="Arrange follow-up and monitor for bleeding or worsening pain.",
        ),
        patient_summary=PatientSummary(
            what_was_discussed="You reported abdominal pain and nausea that started yesterday.",
            what_the_doctor_may_check_next=["A blood test if symptoms continue."],
            what_you_should_do_next=["Follow up within 48 hours if symptoms persist."],
            when_to_get_urgent_help=["Get urgent help if you vomit blood or have black stools."],
        ),
    )


def test_bundle_to_json_returns_serialized_bundle():
    payload = json.loads(bundle_to_json(make_bundle()))

    assert payload["soap_note"]["subjective"] == (
        "Patient reports abdominal pain and nausea since yesterday."
    )
    assert payload["patient_summary"]["what_was_discussed"] == (
        "You reported abdominal pain and nausea that started yesterday."
    )


def test_bundle_to_markdown_outputs_stable_sections():
    markdown = bundle_to_markdown(make_bundle())

    assert markdown.startswith("# SOAP Note\n\n## Subjective\n")
    assert "\n## Objective\n" in markdown
    assert "\n# Patient Summary\n\n## What Was Discussed\n" in markdown
    assert "- A blood test if symptoms continue." in markdown
    assert "- Get urgent help if you vomit blood or have black stools." in markdown


def test_bundle_to_markdown_handles_empty_optional_sections():
    bundle = DocumentationBundle(
        soap_note=make_bundle().soap_note,
        patient_summary=PatientSummary(
            what_was_discussed="You reported a mild headache.",
            what_the_doctor_may_check_next=[],
            what_you_should_do_next=[],
            when_to_get_urgent_help=[],
        ),
    )

    markdown = bundle_to_markdown(bundle)

    assert markdown.count("None documented.") == 3


def test_write_bundle_json_persists_exact_rendered_content():
    bundle = make_bundle()
    output_path = Path("tests") / "fixtures" / f"bundle-{uuid4().hex}.json"

    try:
        write_bundle_json(bundle, output_path)

        assert output_path.read_text(encoding="utf-8") == bundle_to_json(bundle)
    finally:
        if output_path.exists():
            output_path.unlink()


def test_write_bundle_markdown_persists_exact_rendered_content():
    bundle = make_bundle()
    output_path = Path("tests") / "fixtures" / f"bundle-{uuid4().hex}.md"

    try:
        write_bundle_markdown(bundle, output_path)

        assert output_path.read_text(encoding="utf-8") == bundle_to_markdown(bundle)
    finally:
        if output_path.exists():
            output_path.unlink()
