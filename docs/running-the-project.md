# Running The Project

This guide summarizes the main ways to run Dr_Assistant in local development.

## CLI

The canonical CLI lives in `src/cli.py`. You can invoke it directly:

```powershell
python -m src.cli analyze --file "path\to\consultation.mp4" --notes "path\to\doctor_notes.txt"
```

If you installed the project with `pip install -e .`, you can also use:

```powershell
dr-assistant analyze --file "path\to\consultation.mp4" --notes "path\to\doctor_notes.txt"
```

### Analyze

Run the full post-consultation pipeline:

```powershell
python -m src.cli analyze --file "path\to\consultation.mp4" --notes "path\to\doctor_notes.txt" --output-dir "outputs\demo_run"
```

If `--output-dir` is omitted, the pipeline creates a timestamped run directory under `outputs/`.

### Transcribe

Run the legacy transcription-only pipeline:

```powershell
python -m src.cli transcribe --input "path\to\consultation.mp4" --output-dir "outputs\transcribe"
```

If `--output-dir` is omitted, this command writes its artifacts to `data/output`.

### Build KB

Rebuild the retrieval knowledge-base artifacts:

```powershell
python -m src.cli build-kb
```

Run this when `data/input/Symptom2Disease.csv` changes or when you need to regenerate the embedding artifacts from scratch.

## API

Start the FastAPI backend from the repository root:

```powershell
uvicorn src.api.main:app --reload
```

Available endpoints:

- `GET /health`
- `POST /analyze`

`POST /analyze` accepts:

- `file`: uploaded consultation media
- `notes`: doctor notes text

The response model is `FinalConsultationBundle`. If the run is blocked at the safety stage, the API returns a structured error with the failed step and message.

## Frontend

The frontend lives in `frontend/`.

Start the Vite dev server:

```powershell
cd frontend
npm install
npm run dev
```

If PowerShell blocks `npm`, use:

```powershell
npm.cmd run dev
```

The frontend proxies `/analyze` and `/health` to `http://127.0.0.1:8000` during local development.

## Docker And Make

The repository includes:

- a backend `Dockerfile`
- a local `docker-compose.yml`
- a root `Makefile` for common workflows

With `OPENAI_API_KEY` set in your environment, start the stack with:

```powershell
make up
```

Common targets:

- `make build`
- `make up`
- `make down`
- `make restart`
- `make logs`
- `make ps`
- `make api-logs`
- `make frontend-logs`
- `make api-shell`
- `make frontend-shell`
- `make kb`
- `make transcribe FILE=path/to/media.mp4 OUTPUT_DIR=outputs/transcribe`
- `make analyze FILE=path/to/media.mp4 NOTES=doctor_notes.txt OUTPUT_DIR=outputs/demo_run`
- `make docker-kb`
- `make docker-transcribe FILE=path/to/media.mp4 OUTPUT_DIR=outputs/transcribe`
- `make docker-analyze FILE=path/to/media.mp4 NOTES=doctor_notes.txt OUTPUT_DIR=outputs/demo_run`

The Compose API service mounts the repository into `/app`, so Docker-backed runs can read input files from the workspace and write outputs back into it.

## Related Docs

- [getting-started.md](getting-started.md)
- [data-and-artifacts.md](data-and-artifacts.md)
- [post-consultation-workflow.md](post-consultation-workflow.md)
- [testing.md](testing.md)
