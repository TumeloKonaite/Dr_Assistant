from __future__ import annotations

import json
import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from src.contracts.consultation import (
    CarePlan,
    ClinicalReasoningOutput,
    ConsultationCase,
    DocumentationBundle,
    DifferentialDiagnosis,
    FinalConsultationBundle,
    PatientSummary,
    RetrievedCondition,
    SoapNote,
)
from src.pipelines.post_consultation_pipeline import (
    PipelineStepError,
    run_post_consultation_pipeline,
)


def make_case() -> ConsultationCase:
    return ConsultationCase(
        patient_id="P-9001",
        chief_complaint="Headache",
        symptoms=["headache", "fatigue"],
        duration="3 days",
        severity="moderate",
        medications=["ibuprofen"],
        allergies=[],
        history=["migraine"],
        risk_factors=["stress"],
        transcript="Patient reports 3 days of headache and fatigue.",
    )


def make_retrieved() -> list[RetrievedCondition]:
    return [
        RetrievedCondition(
            name="migraine",
            description="A recurrent primary headache disorder.",
            matched_symptoms=["headache"],
            score=0.88,
        )
    ]


def make_reasoning() -> ClinicalReasoningOutput:
    return ClinicalReasoningOutput(
        differentials=[
            DifferentialDiagnosis(
                condition_name="migraine",
                likelihood="moderate",
                reasoning="The symptom pattern is compatible with migraine, but more history is still needed.",
                supporting_findings=["headache", "history of migraine"],
                conflicting_findings=["No neurologic exam findings are available."],
                missing_information=["visual symptoms", "neurologic exam"],
                recommended_tests=[],
                urgency=None,
            )
        ],
        care_plan=CarePlan(
            suggested_tests=[],
            suggested_referrals=["Primary care"],
            follow_up=["Review headache pattern and reassess if symptoms worsen."],
            red_flags=["new neurologic deficit", "sudden severe headache"],
            patient_advice=["Seek urgent help if red-flag symptoms develop."],
            rationale="The available information supports conservative follow-up while watching for urgent features.",
        ),
    )


def make_documentation() -> DocumentationBundle:
    return DocumentationBundle(
        soap_note=SoapNote(
            subjective="Patient reports 3 days of headache and fatigue.",
            objective="No vital signs, examination findings, laboratory results, or imaging results were available in the source materials.",
            assessment="Migraine remains one possible explanation pending fuller assessment.",
            plan="Review symptoms, monitor for red flags, and follow up if the pattern changes.",
        ),
        patient_summary=PatientSummary(
            what_was_discussed="You described a headache and fatigue that have lasted about 3 days.",
            what_the_doctor_may_check_next=["More questions about the headache pattern and any warning signs."],
            what_you_should_do_next=["Follow up if the headache worsens or changes."],
            when_to_get_urgent_help=["Get urgent help for a sudden severe headache or new neurologic symptoms."],
        ),
    )


def make_workspace_dir(prefix: str) -> Path:
    path = Path(".tmp") / f"{prefix}-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_run_post_consultation_pipeline_returns_bundle_and_writes_outputs(
    monkeypatch,
):
    transcript = "Patient reports 3 days of headache and fatigue."
    case = make_case()
    retrieved = make_retrieved()
    reasoning = make_reasoning()
    documentation = make_documentation()
    workspace_dir = make_workspace_dir("post-consultation-success")

    try:
        monkeypatch.setattr(
            "src.pipelines.post_consultation_pipeline.transcribe_consultation",
            lambda file_path: transcript,
        )
        monkeypatch.setattr(
            "src.pipelines.post_consultation_pipeline.extract_consultation_case",
            lambda transcript_text, doctor_notes: case,
        )
        monkeypatch.setattr(
            "src.pipelines.post_consultation_pipeline.retrieve_conditions",
            lambda extracted_case: retrieved,
        )
        monkeypatch.setattr(
            "src.pipelines.post_consultation_pipeline.run_planner",
            lambda extracted_case, retrieved_conditions: reasoning,
        )
        monkeypatch.setattr(
            "src.pipelines.post_consultation_pipeline.run_documentation",
            lambda extracted_case, differentials, care_plan: documentation,
        )

        output_dir = workspace_dir / "outputs"
        bundle = run_post_consultation_pipeline(
            file_path="consult.mp4",
            doctor_notes="Headache started 3 days ago.",
            output_dir=str(output_dir),
        )

        assert isinstance(bundle, FinalConsultationBundle)
        assert bundle.case == case
        assert bundle.differentials == reasoning.differentials
        assert bundle.care_plan == reasoning.care_plan
        assert bundle.soap_note == documentation.soap_note
        assert bundle.patient_summary == documentation.patient_summary

        expected_files = [
            "transcript.txt",
            "case.json",
            "retrieved.json",
            "differentials.json",
            "plan.json",
            "soap.md",
            "patient_summary.md",
            "final_bundle.json",
            "metadata.json",
        ]

        for filename in expected_files:
            assert (output_dir / filename).exists()

        final_bundle_payload = json.loads(
            (output_dir / "final_bundle.json").read_text(encoding="utf-8")
        )
        assert final_bundle_payload["case"]["chief_complaint"] == "Headache"
        assert final_bundle_payload["differentials"][0]["condition_name"] == "migraine"

        metadata = json.loads((output_dir / "metadata.json").read_text(encoding="utf-8"))
        assert metadata["status"] == "completed"
        assert metadata["doctor_notes_provided"] is True
        assert "final_bundle" in metadata["artifacts"]
    finally:
        shutil.rmtree(workspace_dir, ignore_errors=True)


def test_run_post_consultation_pipeline_wraps_step_failures_and_stops(
    monkeypatch,
):
    workspace_dir = make_workspace_dir("post-consultation-failure")

    try:
        monkeypatch.setattr(
            "src.pipelines.post_consultation_pipeline.transcribe_consultation",
            lambda file_path: "Patient reports headache.",
        )

        def fail_case_extraction(
            transcript_text: str, doctor_notes: str
        ) -> ConsultationCase:
            raise RuntimeError("model unavailable")

        monkeypatch.setattr(
            "src.pipelines.post_consultation_pipeline.extract_consultation_case",
            fail_case_extraction,
        )

        def unexpected_call(*args, **kwargs):
            raise AssertionError("downstream steps should not run after a failure")

        monkeypatch.setattr(
            "src.pipelines.post_consultation_pipeline.retrieve_conditions",
            unexpected_call,
        )
        monkeypatch.setattr(
            "src.pipelines.post_consultation_pipeline.run_planner",
            unexpected_call,
        )
        monkeypatch.setattr(
            "src.pipelines.post_consultation_pipeline.run_documentation",
            unexpected_call,
        )

        output_dir = workspace_dir / "failed-output"

        with pytest.raises(PipelineStepError, match="case_extraction"):
            run_post_consultation_pipeline(
                file_path="consult.mp4",
                doctor_notes="Headache started today.",
                output_dir=str(output_dir),
            )

        assert (output_dir / "transcript.txt").exists()
        assert not (output_dir / "case.json").exists()

        metadata = json.loads((output_dir / "metadata.json").read_text(encoding="utf-8"))
        assert metadata["status"] == "failed"
        assert metadata["failed_step"] == "case_extraction"
        assert "model unavailable" in metadata["error"]
    finally:
        shutil.rmtree(workspace_dir, ignore_errors=True)
