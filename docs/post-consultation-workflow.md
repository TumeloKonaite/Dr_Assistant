# Post-Consultation Workflow

This document explains how the canonical Dr_Assistant workflow moves from a consultation media file to a final consultation bundle.

The orchestration entry point is `run_post_consultation_pipeline()` in `src/pipelines/post_consultation_pipeline.py`. The same pipeline is exposed through the CLI `analyze` flow and the FastAPI `/analyze` endpoint.

## Workflow Diagram

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

## At A Glance

| Stage | Main input | Main output | Output file |
| --- | --- | --- | --- |
| Transcription | Media file | Normalized transcript text | `transcript.txt` |
| Case Extraction | Transcript + doctor notes | `ConsultationCase` | `case.json` |
| Red Flag Detection | `ConsultationCase` | Detected red flags + summary context | Included later in `safety.json` |
| Retrieval | `ConsultationCase` | Ranked `RetrievedCondition` list | `retrieved.json` |
| Clinical Reasoning | Case + retrieval + safety context | Differentials + care plan | `differentials.json`, `plan.json` |
| Documentation | Case + reasoning + safety context | SOAP note + patient summary | `soap.md`, `patient_summary.md` |
| Safety Guardrails | Case + generated outputs + red flags | `SafetyReport` | `safety.json` |
| Final Consultation Bundle | All approved outputs | `FinalConsultationBundle` | `final_bundle.json` |

## Step By Step

### 1. Media File

The workflow starts with an audio or video file supplied by the user. Supported file extensions are validated before any processing begins.

The current pipeline accepts common consultation media formats such as `wav`, `mp3`, `m4a`, `mp4`, `mov`, and `webm`. If the file does not exist or uses an unsupported extension, the run fails before transcription starts.

### 2. Transcription

The transcription stage converts the source media into cleaned transcript text.

What happens in this stage:

- The input file is validated.
- Audio is normalized when possible.
- The media is chunked into smaller audio segments.
- Each chunk is transcribed.
- Chunk transcripts are merged into one transcript.
- Transcript text is normalized for downstream use.

This stage writes `transcript.txt` to the run output directory.

Purpose of the stage:

- turn raw media into text
- create a stable input for structured extraction
- isolate media handling from the downstream reasoning pipeline

### 3. Case Extraction

Case extraction turns the transcript and doctor notes into a typed `ConsultationCase`.

Inputs:

- normalized transcript text
- optional or required doctor notes, depending on how the pipeline is invoked

Structured fields in the case contract include:

- `patient_id`
- `chief_complaint`
- `symptoms`
- `duration`
- `severity`
- `medications`
- `allergies`
- `history`
- `risk_factors`
- `transcript`

Important behavior:

- the transcript must be non-empty
- the model response is validated against the `ConsultationCase` schema
- the final case object is forced to carry the original transcript so the contract stays self-contained

This stage writes `case.json`.

Purpose of the stage:

- convert free text into a predictable structure
- separate factual extraction from downstream reasoning
- give every later step a typed contract instead of raw transcript text

### 4. Red Flag Detection

Red flag detection runs on the structured case before retrieval and reasoning.

This step is deterministic. It does not generate diagnoses. Instead, it scans the case fields and transcript for urgent patterns that should stay visible in later outputs.

The current detector looks for patterns such as:

- chest pain with shortness of breath or syncope
- severe headache with neurologic symptoms
- possible gastrointestinal bleeding
- severe shortness of breath
- suicidal ideation or self-harm language

Outputs from this stage:

- a list of `DetectedRedFlag` objects
- a summary string used as downstream safety context

This step does not write a standalone intermediate file. Its results are carried forward into reasoning, documentation, and the final `safety.json` report.

Purpose of the stage:

- preserve urgent context early
- keep risky presentations visible across later text generation
- support patient-facing safety messaging

### 5. Retrieval

Retrieval finds clinically relevant candidate conditions from the local knowledge base.

How retrieval works:

- a short query is built from the case `chief_complaint`, `symptoms`, and `duration`
- prebuilt KB artifacts are loaded from `data/output/`
- the query is embedded
- the most similar conditions are ranked and returned

Each retrieved item is a `RetrievedCondition` with:

- `name`
- `description`
- `matched_symptoms`
- `score`

This stage writes `retrieved.json`.

Purpose of the stage:

- ground downstream reasoning in retrieved candidates
- keep reasoning separate from knowledge-base search
- provide ranked, explainable retrieval evidence instead of a direct diagnosis

### 6. Clinical Reasoning

Clinical reasoning consumes the structured case, retrieved candidates, and red-flag summary.

This stage is split into two linked outputs:

- differential generation
- care-plan generation

The resulting `ClinicalReasoningOutput` contains:

- `differentials`
- `care_plan`

Each differential records:

- condition name
- likelihood
- reasoning
- supporting findings
- conflicting findings
- missing information
- recommended tests
- urgency guidance

The care plan records:

- suggested tests
- suggested referrals
- follow-up recommendations
- red flags to communicate
- patient advice
- rationale

This stage writes:

- `differentials.json`
- `plan.json`

Purpose of the stage:

- turn retrieved candidates into structured differential reasoning
- keep uncertainty explicit
- produce planning output without making definitive unsupported claims

### 7. Documentation

Documentation converts the structured reasoning outputs into clinician-facing and patient-facing artifacts.

Inputs:

- `ConsultationCase`
- differential list
- care plan
- red-flag safety context

Outputs:

- `SoapNote`
- `PatientSummary`

The SOAP note is intended for clinician review. The patient summary is intended to explain what was discussed, what may happen next, what the patient should do next, and when urgent help is needed.

This stage writes:

- `soap.md`
- `patient_summary.md`

Purpose of the stage:

- transform structured reasoning into usable documentation
- keep clinician and patient outputs aligned with the same trusted structured inputs
- avoid introducing new facts, diagnoses, or treatment instructions

### 8. Safety Guardrails

Safety guardrails run after the documentation stage and before the final bundle is approved.

This stage combines three safety inputs:

- detected red flags
- unsafe output checks
- uncertainty calibration

### Unsafe Output Checks

The unsafe-output checker looks for content that should not appear in generated outputs, including:

- definitive diagnosis claims
- invented vitals, exam findings, labs, or imaging
- unsupported medication or dosing instructions
- unsupported treatment or disposition commands
- missing carry-through of urgent red flags in the patient summary

### Uncertainty Calibration

The uncertainty-calibration step checks whether the reasoning matches the amount of evidence available. It looks for issues such as:

- sparse cases described too confidently
- missing-information fields not documented
- high-likelihood differentials with weak support

### Safety Report Outcome

These results are merged into a `SafetyReport` with:

- overall `status`
- `red_flags`
- `red_flag_summary`
- `issues`
- `uncertainty_assessment`
- warning and blocker counts

This stage writes `safety.json`.

If the safety report contains blockers, the pipeline stops here and records the failure as `safety_guardrails` in `metadata.json`. In that case, no `final_bundle.json` is written.

Purpose of the stage:

- stop unsafe or unsupported output from being packaged as final
- preserve diagnostic uncertainty
- make red flags and failure reasons explicit

### 9. Final Consultation Bundle

If no safety blockers are present, the pipeline assembles the final typed bundle.

The `FinalConsultationBundle` contains:

- `case`
- `differentials`
- `care_plan`
- `soap_note`
- `patient_summary`
- `safety`

This stage writes `final_bundle.json`.

Purpose of the stage:

- provide one canonical machine-readable output
- bundle all approved downstream artifacts together
- make API and CLI consumers read from a single final object

## Output Directory Structure

Each run writes into a timestamped output directory under `outputs/` unless another output directory is supplied.

Typical artifacts are:

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

`metadata.json` is updated throughout the run and tracks:

- pipeline name and version
- start and completion timestamps
- input file path
- whether doctor notes were provided
- artifact paths
- failure step and error message when the run fails

## Design Intent

The workflow intentionally separates:

- media processing
- structured extraction
- retrieval
- clinical reasoning
- documentation
- safety review

That separation makes the pipeline easier to validate, test, and inspect. It also reduces the risk of collapsing everything into one opaque generation step.

For the agent-level view of those stage boundaries, see [agents.md](agents.md).
