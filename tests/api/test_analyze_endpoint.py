from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.api.main import app
from src.contracts.consultation import (
    CarePlan,
    ConsultationCase,
    DifferentialDiagnosis,
    FinalConsultationBundle,
    PatientSummary,
    SoapNote,
)
from src.pipelines.post_consultation_pipeline import PipelineStepError


client = TestClient(app)


def make_bundle() -> FinalConsultationBundle:
    return FinalConsultationBundle(
        case=ConsultationCase(
            patient_id="P-1000",
            chief_complaint="Cough",
            symptoms=["cough", "fatigue"],
            duration="1 week",
            severity="moderate",
            transcript="Patient reports cough and fatigue for one week.",
        ),
        differentials=[
            DifferentialDiagnosis(
                condition_name="viral upper respiratory infection",
                likelihood="moderate",
                reasoning="The symptom pattern fits a viral respiratory illness, but the evaluation is incomplete.",
                supporting_findings=["cough", "fatigue"],
                conflicting_findings=["No examination findings are available."],
                missing_information=["temperature", "lung exam"],
                recommended_tests=[],
                urgency=None,
            )
        ],
        care_plan=CarePlan(
            suggested_tests=[],
            suggested_referrals=[],
            follow_up=["Follow up if symptoms persist or worsen."],
            red_flags=["shortness of breath", "high fever"],
            patient_advice=["Rest, hydrate, and seek review if symptoms escalate."],
            rationale="The current information supports conservative follow-up with clear return precautions.",
        ),
        soap_note=SoapNote(
            subjective="Patient reports cough and fatigue for one week.",
            objective="No vitals or examination findings are available in the provided materials.",
            assessment="A viral respiratory illness is one possible explanation.",
            plan="Supportive care and reassessment if symptoms worsen.",
        ),
        patient_summary=PatientSummary(
            what_was_discussed="You described a cough and fatigue that have lasted about one week.",
            what_the_doctor_may_check_next=["More questions or an exam if symptoms continue."],
            what_you_should_do_next=["Rest, hydrate, and follow up if you are not improving."],
            when_to_get_urgent_help=["Get urgent help for trouble breathing or rapidly worsening symptoms."],
        ),
    )


def test_healthcheck_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_endpoint_saves_upload_runs_pipeline_and_cleans_up(monkeypatch):
    bundle = make_bundle()
    captured: dict[str, object] = {}

    def fake_run_post_consultation_pipeline(
        file_path: str,
        doctor_notes: str,
    ) -> FinalConsultationBundle:
        temp_path = Path(file_path)
        captured["path"] = temp_path
        captured["notes"] = doctor_notes
        captured["exists_during_call"] = temp_path.exists()
        return bundle

    monkeypatch.setattr(
        "src.api.main.run_post_consultation_pipeline",
        fake_run_post_consultation_pipeline,
    )

    response = client.post(
        "/analyze",
        files={"file": ("consultation.mp4", b"mock-audio", "video/mp4")},
        data={"notes": "Persistent cough for one week."},
    )

    assert response.status_code == 200
    assert response.json() == bundle.model_dump(mode="json")
    assert captured["notes"] == "Persistent cough for one week."
    assert captured["exists_during_call"] is True
    assert isinstance(captured["path"], Path)
    assert captured["path"].suffix == ".mp4"
    assert captured["path"].exists() is False


def test_analyze_endpoint_returns_structured_safety_guardrail_error(monkeypatch):
    def fake_run_post_consultation_pipeline(
        file_path: str,
        doctor_notes: str,
    ) -> FinalConsultationBundle:
        raise PipelineStepError(
            "safety_guardrails",
            "Generated output introduces vitals, labs, imaging, or examination findings that are not present in the source inputs.",
        )

    monkeypatch.setattr(
        "src.api.main.run_post_consultation_pipeline",
        fake_run_post_consultation_pipeline,
    )

    response = client.post(
        "/analyze",
        files={"file": ("consultation.mp4", b"mock-audio", "video/mp4")},
        data={"notes": "Persistent cough for one week."},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": {
            "step": "safety_guardrails",
            "message": "Generated output introduces vitals, labs, imaging, or examination findings that are not present in the source inputs.",
        }
    }
