# Dr_Assistant

[![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-transcription%20%2B%20reasoning-412991?logo=openai&logoColor=white)](https://platform.openai.com/)
[![Pydantic](https://img.shields.io/badge/Pydantic-typed%20contracts-E92063?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![Pytest](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)](https://docs.pytest.org/)

Dr_Assistant is a clinical post-consultation pipeline for turning consultation audio or video into structured reasoning and documentation artifacts. The current repo includes a canonical CLI pipeline, a FastAPI backend, and a React frontend for local development.

## What It Does

The canonical workflow takes:

- a consultation media file
- optional or required doctor notes, depending on how you invoke it

It produces:

- a transcript
- a structured consultation case
- retrieved clinical candidates
- differential diagnoses
- a care plan
- a SOAP note
- a patient summary
- a safety report
- a final JSON bundle

## Pipeline Overview

```text
Media File
   |
   v
Transcription
   |
   v
Case Extraction
   |
   v
Red Flag Detection
   |
   v
Retrieval
   |
   v
Clinical Reasoning
   |
   v
Documentation
   |
   v
Safety Guardrails
   |
   v
Final Consultation Bundle
```

## Repository Entry Points

- `src/cli.py`: unified CLI with `analyze`, `transcribe`, and `build-kb` subcommands
- `src/rag/build_kb_artifacts.py`: knowledge-base artifact builder implementation
- `src/api/main.py`: FastAPI app with `/health` and `/analyze`
- `frontend/`: React + Vite frontend

## Requirements

- Python `3.12+`
- Node.js and npm for the frontend
- `ffmpeg` available on `PATH`
- `OPENAI_API_KEY` set in your environment

## Installation

Install Python dependencies from the repo root:

```powershell
pip install -r requirements.txt
```

To install the package in editable mode and register the `dr-assistant` CLI:

```powershell
pip install -e .
```

Install the native runtime tools separately and ensure this command resolves on your shell `PATH`:

```powershell
ffmpeg -version
```

If you use a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set your OpenAI API key:

```powershell
setx OPENAI_API_KEY "your_api_key_here"
```

Open a new shell after `setx` so the variable is available to the app.

## Knowledge Base Assets

The repository tracks the canonical retrieval dataset and the generated KB artifacts:

- `data/input/Symptom2Disease.csv`
- `data/output/kb.pkl`
- `data/output/kb_texts.pkl`
- `data/output/kb_embeddings.pt`

Other files under `data/output/` are treated as local generated artifacts and remain ignored.

If you update `data/input/Symptom2Disease.csv`, regenerate the KB artifacts with:

```powershell
python -m src.cli build-kb
```

The build reads `data/input/Symptom2Disease.csv` and rewrites the three files in `data/output/`. On a fresh environment, the embedding model may be downloaded the first time this command runs.

## Canonical CLI Usage

The unified CLI lives in `src/cli.py`. You can invoke it either through the installed `dr-assistant` command or through `python -m src.cli`.

```powershell
python -m src.cli analyze --file "Zeno Minutes.mp4" --notes ".\doctor_notes.txt"
```

To control where artifacts are written:

```powershell
python -m src.cli analyze --file "Zeno Minutes.mp4" --notes ".\doctor_notes.txt" --output-dir ".\outputs\demo_run"
```

By default, the pipeline writes artifacts to a timestamped directory under `outputs/`, for example:

```text
outputs/20260330_153739/
```

If you installed the package with `pip install -e .`, the equivalent command is:

```powershell
dr-assistant analyze --file "Zeno Minutes.mp4" --notes ".\doctor_notes.txt"
```

## Other CLI Commands

Legacy transcription-only workflow:

```powershell
python -m src.cli transcribe --input "Zeno Minutes.mp4"
```

Knowledge-base artifact build:

```powershell
python -m src.cli build-kb
```

This rebuilds `data/output/kb.pkl`, `data/output/kb_texts.pkl`, and `data/output/kb_embeddings.pt` from `data/input/Symptom2Disease.csv`.

## API Usage

Start the backend from the repo root:

```powershell
uvicorn src.api.main:app --reload
```

Available endpoints:

- `GET /health`
- `POST /analyze`

`POST /analyze` accepts:

- `file`: uploaded consultation media
- `notes`: form field containing doctor notes text

The response model is `FinalConsultationBundle`.

## Frontend Usage

The frontend lives in `frontend/`, not the repo root.

Start the frontend dev server like this:

```powershell
cd frontend
npm install
npm run dev
```

If PowerShell blocks `npm`, use:

```powershell
npm.cmd run dev
```

The Vite app proxies `/analyze` and `/health` to `http://127.0.0.1:8000`.

## Output Artifacts

A successful post-consultation run writes files like these:

```text
outputs/<timestamp>/
- case.json
- differentials.json
- final_bundle.json
- metadata.json
- patient_summary.md
- plan.json
- retrieved.json
- safety.json
- soap.md
- transcript.txt
```

`metadata.json` tracks run status, timestamps, input path, output directory, and artifact locations.

## Testing

Run the test suite from the repo root:

```powershell
python -m pytest tests -v
```

## Notes

- Safety guardrails can block final output generation if the system detects unsupported or unsafe claims.
- The API returns structured safety errors for blocked runs.
- Generated markdown artifacts are intended for review, not as definitive medical advice.
