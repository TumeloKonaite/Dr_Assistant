from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

import src.cli as cli
from src.contracts.consultation import (
    CarePlan,
    ConsultationCase,
    DifferentialDiagnosis,
    FinalConsultationBundle,
    PatientSummary,
    SoapNote,
)


def make_bundle() -> FinalConsultationBundle:
    case = ConsultationCase(
        chief_complaint="Cough",
        symptoms=["cough"],
        transcript="Patient reports cough for one week.",
    )
    differentials = [
        DifferentialDiagnosis(
            condition_name="viral upper respiratory infection",
            likelihood="moderate",
            reasoning="The symptom pattern is compatible with a viral respiratory illness.",
            supporting_findings=["cough"],
            conflicting_findings=[],
            missing_information=["fever", "exam findings"],
            recommended_tests=[],
            urgency=None,
        )
    ]
    care_plan = CarePlan(
        suggested_tests=[],
        suggested_referrals=[],
        follow_up=["Follow up if symptoms persist."],
        red_flags=["shortness of breath"],
        patient_advice=["Rest and monitor symptoms."],
        rationale="Supportive care is reasonable while monitoring for deterioration.",
    )
    soap_note = SoapNote(
        subjective="Patient reports cough for one week.",
        objective="No vital signs, examination findings, laboratory results, or imaging results were available in the source materials.",
        assessment="Viral upper respiratory infection is one possible explanation.",
        plan="Supportive care and follow-up if symptoms worsen.",
    )
    patient_summary = PatientSummary(
        what_was_discussed="You reported a cough lasting about a week.",
        what_the_doctor_may_check_next=[
            "Whether you have any fever or breathing trouble."
        ],
        what_you_should_do_next=["Follow up if symptoms persist or worsen."],
        when_to_get_urgent_help=["Get urgent help if you develop shortness of breath."],
    )
    return FinalConsultationBundle(
        case=case,
        differentials=differentials,
        care_plan=care_plan,
        soap_note=soap_note,
        patient_summary=patient_summary,
    )


def make_workspace_dir(prefix: str) -> Path:
    path = Path(".tmp") / f"{prefix}-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_cli_analyze_runs_pipeline_and_prints_summary(monkeypatch, capsys):
    workspace_dir = make_workspace_dir("cli-analyze-success")
    notes_path = workspace_dir / "notes.txt"
    notes_path.write_text("Patient has had a cough for one week.", encoding="utf-8")
    output_dir_path = workspace_dir / "outputs" / "run_001"

    try:

        def fake_run_pipeline(file_path: str, doctor_notes: str, output_dir: str):
            assert file_path == "consult.mp4"
            assert doctor_notes == "Patient has had a cough for one week."
            assert output_dir == str(output_dir_path)
            return make_bundle()

        monkeypatch.setattr(cli, "build_output_dir_path", lambda: output_dir_path)
        monkeypatch.setattr(cli, "run_post_consultation_pipeline", fake_run_pipeline)

        exit_code = cli.main(
            ["analyze", "--file", "consult.mp4", "--notes", str(notes_path)]
        )
        captured = capsys.readouterr()

        assert exit_code == 0
        assert "Pipeline completed successfully." in captured.out
        assert f"Outputs saved to {output_dir_path}" in captured.out
        assert "Chief complaint: Cough" in captured.out
        assert captured.err == ""
    finally:
        shutil.rmtree(workspace_dir, ignore_errors=True)


def test_cli_transcribe_passes_output_dir(monkeypatch, capsys):
    calls: list[tuple[str, str]] = []

    def fake_run_transcription_pipeline(
        input_file: str, output_dir: str = "data/output"
    ) -> str:
        calls.append((input_file, output_dir))
        return "transcript"

    monkeypatch.setattr(
        cli,
        "run_legacy_transcription_pipeline",
        fake_run_transcription_pipeline,
    )

    exit_code = cli.main(
        [
            "transcribe",
            "--input",
            "consult.mp4",
            "--output-dir",
            "custom/output",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert calls == [("consult.mp4", "custom/output")]
    assert captured.err == ""


def test_cli_build_kb_runs_builder(monkeypatch, capsys):
    called = False

    def fake_build_kb() -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(cli, "build_kb_artifacts_main", fake_build_kb)

    exit_code = cli.main(["build-kb"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called is True
    assert captured.err == ""
