# Data And Artifacts

This guide explains the repository data inputs, retrieval assets, and generated output files.

## Knowledge-Base Inputs

The canonical retrieval dataset tracked in the repository is:

- `data/input/Symptom2Disease.csv`

The retrieval build process converts that CSV into generated artifacts under `data/output/`.

## Generated KB Artifacts

The repository tracks the canonical generated retrieval artifacts:

- `data/output/kb.pkl`
- `data/output/kb_texts.pkl`
- `data/output/kb_embeddings.pt`

If you update `data/input/Symptom2Disease.csv`, regenerate those files with:

```powershell
python -m src.cli build-kb
```

On a fresh environment, the embedding model may be downloaded the first time the KB build runs.

## Analysis Pipeline Outputs

A successful canonical analysis run writes a timestamped directory under `outputs/` unless another output directory is supplied.

Typical output structure:

```text
outputs/<timestamp>/
  metadata.json
  transcript.txt
  case.json
  retrieved.json
  differentials.json
  plan.json
  soap.md
  patient_summary.md
  safety.json
  final_bundle.json
```

### Output Files

- `metadata.json`: run status, timestamps, input path, output path, and artifact locations
- `transcript.txt`: normalized transcript text
- `case.json`: structured `ConsultationCase`
- `retrieved.json`: ranked retrieval candidates
- `differentials.json`: structured differential list
- `plan.json`: care-plan output
- `soap.md`: clinician-facing SOAP note
- `patient_summary.md`: patient-facing summary
- `safety.json`: red flags, safety issues, and uncertainty assessment
- `final_bundle.json`: final `FinalConsultationBundle`

If the run is blocked during safety guardrails, `safety.json` and `metadata.json` may still be written, but `final_bundle.json` will not be created.

## Transcription-Only Outputs

The legacy transcription-only command writes:

- chunk files under `<output_dir>/chunks/`
- a normalized WAV file when normalization succeeds
- `<media_stem>_transcript.txt`

If no `--output-dir` is supplied to `python -m src.cli transcribe`, the default directory is `data/output`.

## Related Docs

- [running-the-project.md](running-the-project.md)
- [post-consultation-workflow.md](post-consultation-workflow.md)
- [testing-with-synthetic-dataset.md](testing-with-synthetic-dataset.md)
