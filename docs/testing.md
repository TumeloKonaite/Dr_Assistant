# Testing

This guide covers the main testing paths for Dr_Assistant.

## Automated Tests

Run the Python test suite from the repository root:

```powershell
python -m pytest tests -v
```

The repository uses `pytest` and keeps tests under `tests/`.

## Workflow-Focused Testing

The most practical end-to-end checks usually fall into two groups:

- run `python -m src.cli analyze ...` against a representative consultation file
- run `python -m src.cli transcribe ...` when you only want to validate the media and transcription path

Those runs write artifacts under `outputs/` or a supplied output directory, which makes it easy to inspect transcripts, cases, reasoning artifacts, and safety results after each run.

## Synthetic Dataset

For repeatable local evaluation with realistic synthetic data, use:

- [testing-with-synthetic-dataset.md](testing-with-synthetic-dataset.md)

That guide walks through downloading the synthetic consultation dataset, exploring its files, and running both transcription-only and full pipeline checks against the repository.
