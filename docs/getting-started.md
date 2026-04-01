# Getting Started

This guide covers the baseline setup required to run Dr_Assistant locally.

## Requirements

- Python `3.12+`
- `ffmpeg` available on your shell `PATH`
- `OPENAI_API_KEY` set in your environment
- Node.js and npm if you want to run the frontend

Check that `ffmpeg` is installed:

```powershell
ffmpeg -version
```

## Python Setup

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If you want the `dr-assistant` command registered in your environment, install the project in editable mode:

```powershell
pip install -e .
```

## Environment Variables

Set the OpenAI API key:

```powershell
setx OPENAI_API_KEY "your_api_key_here"
```

Open a new shell after `setx` so the variable is available to Python, Uvicorn, and Docker commands launched from the terminal.

## First Run

Create a plain-text doctor notes file, then run:

```powershell
python -m src.cli analyze --file "path\to\consultation.mp4" --notes "path\to\doctor_notes.txt"
```

By default, the canonical analysis pipeline writes artifacts into a timestamped directory under `outputs/`.

## Project Entry Points

- `src/cli.py`: unified CLI for `analyze`, `transcribe`, and `build-kb`
- `src/api/main.py`: FastAPI app with `/health` and `/analyze`
- `frontend/`: React + Vite frontend
- `src/pipelines/post_consultation_pipeline.py`: canonical workflow orchestration

## Related Docs

- [running-the-project.md](running-the-project.md)
- [data-and-artifacts.md](data-and-artifacts.md)
- [post-consultation-workflow.md](post-consultation-workflow.md)
