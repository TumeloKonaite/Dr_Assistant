# Agents

This guide describes the agent layer in Dr_Assistant, what each agent is responsible for, and how those agent wrappers relate to the canonical pipeline.

## Why The Repository Has Agents

The repository uses agent wrappers to define narrow, typed responsibilities around specific clinical post-consultation tasks. Each agent is intentionally limited in scope and delegates its real work to validated tool functions and typed contracts.

That keeps the system easier to test and reason about than a single unconstrained generation step.

## Current Agent Catalog

| Agent | File | Function-tool wrapper | Lower-level tool calls | Output | Used in canonical pipeline |
| --- | --- | --- | --- | --- | --- |
| `case_builder_agent` | `src/agents/case_builder_agent.py` | `case_extraction_tool(...)` | `extract_consultation_case(...)` | Structured case payload | Not directly |
| `retrieval_agent` | `src/agents/retrieval_agent.py` | `retrieve_conditions_tool(...)` | `retrieve_conditions(...)` | `RetrievedCondition[]` | Not directly |
| `differential_agent` | `src/agents/differential_agent.py` | `differential_generation_tool(...)` | `generate_differentials(...)` | `DifferentialDiagnosis[]` | Indirectly via planner logic |
| `planner_agent` | `src/agents/planner_agent.py` | `planner_tool(...)` | `generate_differentials(...)`, `generate_care_plan(...)` | `ClinicalReasoningOutput` | Yes |
| `documentation_agent` | `src/agents/documentation_agent.py` | `documentation_tool(...)` | `generate_soap(...)`, `generate_patient_summary(...)` | `DocumentationBundle` | Yes |

## How Agents Fit Into The Pipeline

The canonical post-consultation pipeline is orchestrated in `src/pipelines/post_consultation_pipeline.py`.

Today, the pipeline uses a mix of direct tool calls and agent-layer helper functions:

- case extraction currently calls `extract_consultation_case(...)` directly
- retrieval currently calls `retrieve_conditions(...)` directly
- clinical reasoning uses `run_planner(...)`
- documentation uses `run_documentation(...)`

That means the repository has reusable agent definitions for several stages, but the current orchestration path only depends directly on the planner and documentation agent helpers.

## Agent By Agent

### Case Builder Agent

`case_builder_agent` wraps the case-extraction tool and exists to convert transcript text plus doctor notes into a structured consultation case.

Responsibility:

- extract evidence-grounded structured case data
- return a schema-aligned case payload

Input shape:

- `transcript_text`
- `doctor_notes`

Function-tool wrapper:

- `case_extraction_tool(...)`

Lower-level tool call:

- `extract_consultation_case(...)`

Notes:

- this agent is a thin wrapper around the case-extraction tool
- the canonical pipeline currently calls the tool directly instead of invoking the agent object

### Retrieval Agent

`retrieval_agent` is responsible for retrieval only. It takes a structured case and returns ranked illness candidates from the local knowledge base.

Responsibility:

- perform retrieval and ranking only
- avoid diagnosis, treatment, or care-plan generation

Input shape:

- `ConsultationCase`
- optional `top_k`

Function-tool wrapper:

- `retrieve_conditions_tool(...)`

Lower-level tool call:

- `retrieve_conditions(...)`

Notes:

- this agent is intentionally constrained to retrieval boundaries
- the canonical pipeline currently calls the retrieval function directly

### Differential Agent

`differential_agent` generates structured differential diagnoses from a structured case plus retrieved candidates.

Responsibility:

- produce schema-compliant differentials
- preserve diagnostic uncertainty
- avoid definitive diagnosis language

Input shape:

- `ConsultationCase`
- `RetrievedCondition[]`

Function-tool wrapper:

- `differential_generation_tool(...)`

Lower-level tool call:

- `generate_differentials(...)`

Notes:

- this is a narrower reasoning wrapper
- the canonical pipeline reaches this logic through `run_planner(...)` rather than calling the differential agent object directly

### Planner Agent

`planner_agent` coordinates the full clinical reasoning stage after retrieval.

Responsibility:

- generate differentials first
- generate a care plan from those differentials
- keep reasoning structured and non-definitive

Input shape:

- `ConsultationCase`
- `RetrievedCondition[]`
- optional `safety_context`

Output:

- `ClinicalReasoningOutput`

Function-tool wrapper:

- `planner_tool(...)`

Lower-level tool calls:

- `generate_differentials(...)`
- `generate_care_plan(...)`

Notes:

- this is the primary reasoning coordinator used by the canonical pipeline
- the pipeline imports `run_planner(...)` rather than invoking the `planner_agent` object directly

### Documentation Agent

`documentation_agent` coordinates the documentation stage after reasoning has completed.

Responsibility:

- generate a SOAP note
- generate a patient summary
- keep outputs grounded in trusted structured inputs
- avoid invented findings, definitive diagnoses, or treatment instructions

Input shape:

- `ConsultationCase`
- `DifferentialDiagnosis[]`
- `CarePlan`
- optional `safety_context`

Output:

- `DocumentationBundle`

Function-tool wrapper:

- `documentation_tool(...)`

Lower-level tool calls:

- `generate_soap(...)`
- `generate_patient_summary(...)`

Notes:

- this is the primary documentation coordinator used by the canonical pipeline
- the pipeline imports `run_documentation(...)` rather than invoking the `documentation_agent` object directly

## Shared Patterns Across Agents

The current agents follow a common structure:

- define a narrow function-tool wrapper
- have that wrapper call one or more lower-level domain tool functions
- validate inputs and outputs with typed contracts
- keep instructions tightly scoped to one stage
- use `gpt-5-nano` as the configured model

This keeps each agent legible and easier to test than a multi-purpose orchestration prompt.

## Tool Reference By Agent

For quick lookup, the concrete tool calls are:

- `case_builder_agent`: `case_extraction_tool(...)` -> `extract_consultation_case(...)`
- `retrieval_agent`: `retrieve_conditions_tool(...)` -> `retrieve_conditions(...)`
- `differential_agent`: `differential_generation_tool(...)` -> `generate_differentials(...)`
- `planner_agent`: `planner_tool(...)` -> `generate_differentials(...)` + `generate_care_plan(...)`
- `documentation_agent`: `documentation_tool(...)` -> `generate_soap(...)` + `generate_patient_summary(...)`

## Compatibility Layer

The repository uses `src/agents/_compat.py` as a compatibility shim.

Behavior:

- if the `agents` package is available, the real `Agent` and `function_tool` imports are used
- if not, a lightweight fallback class is used for local testing

That lets the codebase keep agent definitions importable in environments where the full agent runtime is not installed or not needed for unit tests.

## Design Intent

The agent layer is meant to preserve boundaries between:

- extraction
- retrieval
- reasoning
- documentation

Those boundaries matter because they reduce hidden coupling, make failures easier to localize, and support stronger safety checks on generated outputs.

## Related Docs

- [post-consultation-workflow.md](post-consultation-workflow.md)
- [running-the-project.md](running-the-project.md)
- [data-and-artifacts.md](data-and-artifacts.md)
