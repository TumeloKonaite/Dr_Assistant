# Dr_Assistant

[![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-transcription%20%2B%20reasoning-412991?logo=openai&logoColor=white)](https://platform.openai.com/)
[![Pydantic](https://img.shields.io/badge/Pydantic-typed%20contracts-E92063?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![Pytest](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)](https://docs.pytest.org/)

Dr_Assistant is a clinical post-consultation pipeline that turns consultation audio or video into structured reasoning and documentation artifacts. The repository includes a canonical Python CLI, a FastAPI backend, and a React frontend for local development.

## Overview

The canonical pipeline takes:

- a consultation media file
- doctor notes text

It produces:

- a transcript
- a structured consultation case
- retrieved clinical candidates
- differential diagnoses
- a care plan
- a SOAP note
- a patient summary
- a safety report
- a final JSON consultation bundle

## Workflow

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

The detailed workflow guide lives in [docs/post-consultation-workflow.md](docs/post-consultation-workflow.md).

## Quick Start

Prerequisites:

- Python `3.12+`
- `ffmpeg` on your `PATH`
- `OPENAI_API_KEY` in your environment
- Node.js and npm if you want to run the frontend

Install the Python dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set your API key:

```powershell
setx OPENAI_API_KEY "your_api_key_here"
```

Open a new shell, reactivate the virtual environment, then run the pipeline:

```powershell
python -m src.cli analyze --file "path\to\consultation.mp4" --notes "path\to\doctor_notes.txt"
```

## Common Entry Points

- CLI: `python -m src.cli analyze --file ... --notes ...`
- API: `uvicorn src.api.main:app --reload`
- Frontend: `cd frontend` then `npm install` and `npm run dev`
- Docker stack: `make up`

## Documentation

- [docs/README.md](docs/README.md): documentation index
- [docs/getting-started.md](docs/getting-started.md): setup, environment, and installation
- [docs/running-the-project.md](docs/running-the-project.md): CLI, API, frontend, Docker, and Make usage
- [docs/data-and-artifacts.md](docs/data-and-artifacts.md): knowledge-base assets and pipeline outputs
- [docs/agents.md](docs/agents.md): agent responsibilities and how they map to the pipeline
- [docs/post-consultation-workflow.md](docs/post-consultation-workflow.md): stage-by-stage workflow explanation
- [docs/testing.md](docs/testing.md): automated and workflow-focused testing
- [docs/testing-with-synthetic-dataset.md](docs/testing-with-synthetic-dataset.md): synthetic dataset testing guide

## Safety Notice

This project is intended as decision-support and documentation software for review by qualified humans. It is not a substitute for licensed clinical judgment, not legal advice, and should not be represented as regulatory clearance or compliance status.

Safety guardrails can block final output generation when the system detects unsupported or unsafe claims.

## License

This repository is licensed under the Apache License 2.0. See [LICENSE](LICENSE).
