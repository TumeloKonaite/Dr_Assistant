from __future__ import annotations

from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Callable, TypeVar

from src.agents.documentation_agent import run_documentation
from src.agents.planner_agent import run_planner
from src.contracts.consultation import FinalConsultationBundle, SafetyIssue, SafetyReport
from src.tools.case_extraction_tool import extract_consultation_case
from src.tools.illness_retrieval_tool import retrieve_conditions
from src.tools.red_flag_detector_tool import detect_red_flags, summarize_red_flags
from src.tools.transcription_tool import transcribe_consultation
from src.tools.uncertainty_calibration_tool import assess_uncertainty
from src.tools.unsafe_output_checker import check_generated_outputs
from src.utils.logging import get_logger
from src.utils.output_writer import (
    ensure_output_dir,
    render_patient_summary,
    render_soap_note,
    write_json_output,
    write_text_output,
)


T = TypeVar("T")


class PipelineStepError(RuntimeError):
    def __init__(self, step: str, message: str):
        self.step = step
        super().__init__(f"Pipeline step '{step}' failed: {message}")


def build_output_dir_path(base_dir: str | Path = "outputs") -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path(base_dir) / timestamp


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _project_version() -> str | None:
    try:
        return version("dr-assistant")
    except PackageNotFoundError:
        return None


def _run_step(step: str, action: Callable[[], T]) -> T:
    logger = get_logger(__name__)
    logger.info("step=%s status=started", step)

    try:
        result = action()
    except Exception as exc:
        logger.exception("step=%s status=failed", step)
        raise PipelineStepError(step, str(exc)) from exc

    logger.info("step=%s status=completed", step)
    return result


def _build_safety_report(
    red_flags,
    unsafe_issues: list[SafetyIssue],
    uncertainty_assessment,
) -> SafetyReport:
    issues = [*unsafe_issues, *uncertainty_assessment.issues]
    blocker_count = sum(1 for issue in issues if issue.severity == "blocker")
    warning_count = sum(1 for issue in issues if issue.severity == "warning")
    status = "blocked" if blocker_count else "warning" if warning_count else "clear"

    return SafetyReport(
        status=status,
        red_flags=red_flags,
        red_flag_summary=summarize_red_flags(red_flags),
        issues=issues,
        uncertainty_assessment=uncertainty_assessment,
        warning_count=warning_count,
        blocker_count=blocker_count,
    )


def run_post_consultation_pipeline(
    file_path: str,
    doctor_notes: str,
    output_dir: str | None = None,
) -> FinalConsultationBundle:
    logger = get_logger(__name__)
    resolved_output_dir = ensure_output_dir(output_dir or build_output_dir_path())

    metadata: dict[str, object] = {
        "pipeline_name": "post_consultation_pipeline",
        "pipeline_version": _project_version(),
        "status": "running",
        "started_at": _utc_timestamp(),
        "input_file_path": str(Path(file_path).resolve()),
        "output_dir": str(resolved_output_dir.resolve()),
        "doctor_notes_provided": bool(doctor_notes.strip()),
        "doctor_notes_characters": len(doctor_notes),
        "artifacts": {},
    }
    metadata_path = resolved_output_dir / "metadata.json"
    write_json_output(metadata_path, metadata)

    logger.info(
        "post-consultation pipeline started input_file=%s output_dir=%s",
        file_path,
        resolved_output_dir,
    )

    try:
        transcript = _run_step(
            "transcription",
            lambda: transcribe_consultation(file_path),
        )
        transcript_path = write_text_output(
            resolved_output_dir / "transcript.txt",
            transcript,
        )
        metadata["artifacts"] = {
            **metadata["artifacts"],
            "transcript": str(transcript_path.resolve()),
        }
        write_json_output(metadata_path, metadata)

        case = _run_step(
            "case_extraction",
            lambda: extract_consultation_case(transcript, doctor_notes),
        )
        case_path = write_json_output(resolved_output_dir / "case.json", case)
        metadata["artifacts"] = {
            **metadata["artifacts"],
            "case": str(case_path.resolve()),
        }
        write_json_output(metadata_path, metadata)

        red_flags = _run_step(
            "red_flag_detection",
            lambda: detect_red_flags(case),
        )
        safety_context = summarize_red_flags(red_flags)

        retrieved = _run_step(
            "retrieval",
            lambda: retrieve_conditions(case),
        )
        retrieved_path = write_json_output(
            resolved_output_dir / "retrieved.json",
            retrieved,
        )
        metadata["artifacts"] = {
            **metadata["artifacts"],
            "retrieved": str(retrieved_path.resolve()),
        }
        write_json_output(metadata_path, metadata)

        reasoning = _run_step(
            "clinical_reasoning",
            lambda: run_planner(case, retrieved, safety_context=safety_context),
        )
        differentials_path = write_json_output(
            resolved_output_dir / "differentials.json",
            reasoning.differentials,
        )
        plan_path = write_json_output(resolved_output_dir / "plan.json", reasoning.care_plan)
        metadata["artifacts"] = {
            **metadata["artifacts"],
            "differentials": str(differentials_path.resolve()),
            "plan": str(plan_path.resolve()),
        }
        write_json_output(metadata_path, metadata)

        documentation = _run_step(
            "documentation",
            lambda: run_documentation(
                case,
                reasoning.differentials,
                reasoning.care_plan,
                safety_context=safety_context,
            ),
        )
        soap_path = write_text_output(
            resolved_output_dir / "soap.md",
            render_soap_note(documentation.soap_note),
        )
        patient_summary_path = write_text_output(
            resolved_output_dir / "patient_summary.md",
            render_patient_summary(documentation.patient_summary),
        )
        metadata["artifacts"] = {
            **metadata["artifacts"],
            "soap_note": str(soap_path.resolve()),
            "patient_summary": str(patient_summary_path.resolve()),
        }

        unsafe_issues = _run_step(
            "unsafe_output_check",
            lambda: check_generated_outputs(
                case=case,
                differentials=reasoning.differentials,
                care_plan=reasoning.care_plan,
                soap_note=documentation.soap_note,
                patient_summary=documentation.patient_summary,
                detected_red_flags=red_flags,
            ),
        )
        uncertainty_assessment = _run_step(
            "uncertainty_calibration",
            lambda: assess_uncertainty(case, reasoning.differentials),
        )
        safety_report = _build_safety_report(
            red_flags=red_flags,
            unsafe_issues=unsafe_issues,
            uncertainty_assessment=uncertainty_assessment,
        )
        safety_path = write_json_output(resolved_output_dir / "safety.json", safety_report)
        metadata["artifacts"] = {
            **metadata["artifacts"],
            "safety": str(safety_path.resolve()),
        }

        if safety_report.blocker_count:
            write_json_output(metadata_path, metadata)
            blocker_messages = "; ".join(
                issue.message for issue in safety_report.issues if issue.severity == "blocker"
            )
            raise PipelineStepError("safety_guardrails", blocker_messages)

        bundle = FinalConsultationBundle(
            case=case,
            differentials=reasoning.differentials,
            care_plan=reasoning.care_plan,
            soap_note=documentation.soap_note,
            patient_summary=documentation.patient_summary,
            safety=safety_report,
        )
        final_bundle_path = write_json_output(
            resolved_output_dir / "final_bundle.json",
            bundle,
        )
        metadata["artifacts"] = {
            **metadata["artifacts"],
            "final_bundle": str(final_bundle_path.resolve()),
        }
        metadata["status"] = "completed"
        metadata["completed_at"] = _utc_timestamp()
        write_json_output(metadata_path, metadata)
        logger.info("post-consultation pipeline completed output_dir=%s", resolved_output_dir)
        return bundle
    except PipelineStepError as exc:
        metadata["status"] = "failed"
        metadata["failed_at"] = _utc_timestamp()
        metadata["failed_step"] = exc.step
        metadata["error"] = str(exc)
        write_json_output(metadata_path, metadata)
        logger.exception(
            "post-consultation pipeline failed step=%s output_dir=%s",
            exc.step,
            resolved_output_dir,
        )
        raise
