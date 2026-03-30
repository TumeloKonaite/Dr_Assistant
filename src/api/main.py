from __future__ import annotations

import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status

from src.contracts.consultation import FinalConsultationBundle
from src.pipelines.post_consultation_pipeline import (
    PipelineStepError,
    run_post_consultation_pipeline,
)


app = FastAPI(title="Dr Assistant API")


def _pipeline_error_message(exc: PipelineStepError) -> str:
    prefix = f"Pipeline step '{exc.step}' failed: "
    message = str(exc)
    return message[len(prefix) :] if message.startswith(prefix) else message


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=FinalConsultationBundle)
def analyze_consultation(
    file: UploadFile = File(...),
    notes: str = Form(default=""),
) -> FinalConsultationBundle:
    suffix = Path(file.filename or "consultation-upload").suffix

    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_path = Path(temp_file.name)

    try:
        try:
            return run_post_consultation_pipeline(
                file_path=str(temp_path),
                doctor_notes=notes,
            )
        except PipelineStepError as exc:
            status_code = (
                status.HTTP_422_UNPROCESSABLE_CONTENT
                if exc.step == "safety_guardrails"
                else status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            raise HTTPException(
                status_code=status_code,
                detail={
                    "step": exc.step,
                    "message": _pipeline_error_message(exc),
                },
            ) from exc
    finally:
        file.file.close()
        temp_path.unlink(missing_ok=True)
