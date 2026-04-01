# Testing With The Synthetic Consultation Dataset

This repository can be exercised with the public Hugging Face dataset [`TumeloKonaite/synthetic-patient-dr-data`](https://huggingface.co/datasets/TumeloKonaite/synthetic-patient-dr-data).

The dataset is explicitly synthetic and intended for research and prototyping, not real patient care. As of March 31, 2026, the dataset page reports:

- `train` split only
- `50` exported consultations
- English (`en`) with South African English accent targets
- full-consultation WAV audio under `audio/`
- structured rows in `data/train.jsonl`
- supporting transcript and manifest files under `transcripts/` and `manifests/`

## 1. Download The Dataset

The easiest scripted option is `huggingface_hub`:

```powershell
pip install huggingface_hub
python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='TumeloKonaite/synthetic-patient-dr-data', repo_type='dataset', local_dir='data/external/synthetic-patient-dr-data')"
```

That command downloads the dataset into:

```text
data/external/synthetic-patient-dr-data/
```

If you prefer the browser, you can also inspect or download files directly from the dataset page:

- Dataset page: `https://huggingface.co/datasets/TumeloKonaite/synthetic-patient-dr-data`
- Source repository linked by the dataset card: `https://github.com/TumeloKonaite/synthetic_data`

## 2. Explore The Files

After download, the most useful paths are:

- `data/external/synthetic-patient-dr-data/data/train.jsonl`
- `data/external/synthetic-patient-dr-data/audio/consult_000000/full.wav`
- `data/external/synthetic-patient-dr-data/transcripts/consult_000000.json`
- `data/external/synthetic-patient-dr-data/manifests/consult_000000.json`

List the top-level dataset contents:

```powershell
Get-ChildItem data\external\synthetic-patient-dr-data
```

Inspect the first JSONL row:

```powershell
Get-Content data\external\synthetic-patient-dr-data\data\train.jsonl -First 1
```

Inspect selected fields from the first row in a friendlier format:

```powershell
$row = Get-Content data\external\synthetic-patient-dr-data\data\train.jsonl -First 1 | ConvertFrom-Json
$row | Select-Object consultation_id, split, audio_available, full_transcript
```

Useful nested fields to inspect in `train.jsonl`:

- `scenario`
- `conversation`
- `tts_script`
- `clinical_outputs`
- `quality_labels`
- `full_transcript`
- `audio`

## 3. Run A Transcription Test Against This Repo

This repository already supports transcription-only runs, which is the cleanest way to benchmark the dataset audio against the app.

Use one consultation WAV file:

```powershell
make transcribe FILE=data/external/synthetic-patient-dr-data/audio/consult_000000/full.wav OUTPUT_DIR=outputs/hf_consult_000000
```

If you are not using `make`, the equivalent command is:

```powershell
python -m src.cli transcribe --input "data/external/synthetic-patient-dr-data/audio/consult_000000/full.wav" --output-dir "outputs/hf_consult_000000"
```

The generated transcript can then be compared with:

- `data/external/synthetic-patient-dr-data/transcripts/consult_000000.json`
- the `full_transcript` field in `data/train.jsonl`

## 4. Run The Full Analysis Pipeline

The CLI `analyze` command in this repo requires a doctor-notes text file in addition to the audio input. The dataset gives you enough structured context to create one quickly.

Create a small notes file manually:

```powershell
Set-Content hf_notes.txt "Blood pressure follow-up with intermittent headaches. No nausea, weakness, chest pain, or shortness of breath reported. Home blood pressure roughly 138/86."
```

Then run the full pipeline:

```powershell
make analyze FILE=data/external/synthetic-patient-dr-data/audio/consult_000000/full.wav NOTES=hf_notes.txt OUTPUT_DIR=outputs/hf_analyze_000000
```

Equivalent CLI command:

```powershell
python -m src.cli analyze --file "data/external/synthetic-patient-dr-data/audio/consult_000000/full.wav" --notes "hf_notes.txt" --output-dir "outputs/hf_analyze_000000"
```

When you want richer notes, use the dataset row's structured content as source material, especially:

- `clinical_outputs.clinical_summary`
- `clinical_outputs.derived_artifacts.doctor_summary`
- `scenario.clinical_context`

## 5. Suggested Manual Checks

For a quick qualitative review, compare this repo's outputs with the dataset's reference fields:

- Compare the generated `transcript.txt` to `full_transcript`
- Compare extracted case details to `scenario.clinical_context`
- Compare summarization artifacts to `clinical_outputs`
- Check whether red-flag handling matches the scenario and conversation

## 6. Important Limits

- The retrieval KB in this repository is still built from `data/input/Symptom2Disease.csv`; this dataset is for testing the consultation pipeline, not for replacing the current KB source.
- The dataset is synthetic and should not be treated as evidence of real-world clinical performance.
