import {
  DragEvent,
  FormEvent,
  startTransition,
  useId,
  useState,
} from "react";

type Likelihood = "high" | "moderate" | "lower";
type SafetyStatus = "clear" | "warning" | "blocked";
type WorkspaceView =
  | "overview"
  | "differentials"
  | "plan"
  | "documentation"
  | "safety"
  | "json";

type ConsultationCase = {
  patient_id?: string | null;
  chief_complaint: string;
  symptoms: string[];
  duration?: string | null;
  severity?: string | null;
  medications: string[];
  allergies: string[];
  history: string[];
  risk_factors: string[];
  transcript: string;
};

type DifferentialDiagnosis = {
  condition_name: string;
  likelihood: Likelihood;
  reasoning: string;
  supporting_findings: string[];
  conflicting_findings: string[];
  missing_information: string[];
  recommended_tests: string[];
  urgency?: string | null;
};

type CarePlan = {
  suggested_tests: string[];
  suggested_referrals: string[];
  follow_up: string[];
  red_flags: string[];
  patient_advice: string[];
  rationale: string;
};

type SoapNote = {
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
};

type PatientSummary = {
  what_was_discussed: string;
  what_the_doctor_may_check_next: string[];
  what_you_should_do_next: string[];
  when_to_get_urgent_help: string[];
};

type SafetyIssue = {
  code: string;
  severity: "warning" | "blocker";
  source: string;
  message: string;
  evidence: string[];
};

type DetectedRedFlag = {
  code: string;
  title: string;
  summary: string;
  urgency: "urgent" | "emergent";
  evidence: string[];
  patient_summary_terms: string[];
};

type UncertaintyAssessment = {
  evidence_level: "sparse" | "limited" | "adequate";
  confidence_alignment: "aligned" | "overstated";
  explicit_uncertainty_present: boolean;
  missing_information_documented: boolean;
  supported_high_likelihood_differentials: boolean;
  summary: string;
  issues: SafetyIssue[];
};

type SafetyReport = {
  status: SafetyStatus;
  red_flags: DetectedRedFlag[];
  red_flag_summary: string;
  issues: SafetyIssue[];
  uncertainty_assessment: UncertaintyAssessment;
  warning_count: number;
  blocker_count: number;
};

type FinalConsultationBundle = {
  case: ConsultationCase;
  differentials: DifferentialDiagnosis[];
  care_plan: CarePlan;
  soap_note: SoapNote;
  patient_summary: PatientSummary;
  safety?: SafetyReport | null;
};

type ApiErrorDetail =
  | string
  | {
      step?: string;
      message?: string;
    };

type ApiErrorPayload = {
  detail?: ApiErrorDetail;
};

const VIEW_OPTIONS: Array<{
  id: WorkspaceView;
  label: string;
  shortLabel: string;
}> = [
  { id: "overview", label: "Overview", shortLabel: "Overview" },
  { id: "differentials", label: "Differentials", shortLabel: "Differentials" },
  { id: "plan", label: "Care plan", shortLabel: "Care Plan" },
  { id: "documentation", label: "Documentation", shortLabel: "Documentation" },
  { id: "safety", label: "Safety", shortLabel: "Safety" },
  { id: "json", label: "Raw JSON", shortLabel: "Raw JSON" },
];

const SECTION_PREVIEWS: Array<{
  title: string;
  description: string;
}> = [
  {
    title: "Overview",
    description: "Chief complaint, symptoms, medications, history",
  },
  {
    title: "Differentials",
    description: "Ranked conditions with evidence and reasoning",
  },
  {
    title: "Care Plan",
    description: "Tests, referrals, follow-up, patient advice",
  },
  {
    title: "Documentation",
    description: "SOAP note and patient summary",
  },
  {
    title: "Safety",
    description: "Red flags, warnings, and uncertainty",
  },
];

const TRANSCRIPT_PREVIEW_LIMIT = 320;

function formatApiError(status: number, payload: ApiErrorPayload | null): string {
  const detail = payload?.detail;

  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (detail && typeof detail === "object") {
    const message = detail.message?.trim();
    const step = detail.step?.trim();

    if (message && step === "safety_guardrails") {
      return `Analysis blocked by safety guardrails: ${message}`;
    }

    if (message) {
      return step ? `${step}: ${message}` : message;
    }
  }

  return `Request failed with status ${status}`;
}

function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) {
    return "0 B";
  }

  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1,
  );
  const value = bytes / 1024 ** index;

  return `${value >= 10 || index === 0 ? value.toFixed(0) : value.toFixed(1)} ${units[index]}`;
}

function previewTranscript(transcript: string): string {
  const normalized = transcript.trim().replace(/\s+/g, " ");

  if (normalized.length <= TRANSCRIPT_PREVIEW_LIMIT) {
    return normalized;
  }

  return `${normalized.slice(0, TRANSCRIPT_PREVIEW_LIMIT).trimEnd()}...`;
}

function countWords(text: string): number {
  return text.trim().split(/\s+/).filter(Boolean).length;
}

function UploadIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M12 16V6m0 0-3.5 3.5M12 6l3.5 3.5M5 15.5V18a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function FileIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M14 3H8.5A2.5 2.5 0 0 0 6 5.5v13A2.5 2.5 0 0 0 8.5 21h7A2.5 2.5 0 0 0 18 18.5V7l-4-4Z"
        fill="none"
        stroke="currentColor"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
      <path
        d="M14 3v4h4M8.5 15.5c1.2-1.5 4-1.5 5.2 0m-5.4 2.8c2-2.6 6.5-2.6 8.5 0"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function ShieldIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M12 3.5c1.7 1.3 3.8 2 6 2v5.6c0 4.2-2.5 7.8-6 9.4-3.5-1.6-6-5.2-6-9.4V5.5c2.2 0 4.3-.7 6-2Z"
        fill="none"
        stroke="currentColor"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function BrandMark() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M3 12h4l2-5 3 10 2-5h7"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function ArrowIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M6 12h12M13 7l5 5-5 5"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function ListBlock({
  title,
  items,
  emptyText = "Nothing surfaced in this section.",
}: {
  title: string;
  items: string[];
  emptyText?: string;
}) {
  return (
    <section className="list-block">
      <h3>{title}</h3>
      {items.length ? (
        <ul>
          {items.map((item) => (
            <li key={`${title}-${item}`}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="list-empty">{emptyText}</p>
      )}
    </section>
  );
}

function SafetyTone({ safety }: { safety?: SafetyReport | null }) {
  if (!safety) {
    return <span className="status status-muted">Safety pending</span>;
  }

  return (
    <span className={`status status-${safety.status}`}>
      Safety {safety.status}
    </span>
  );
}

function PreviewCard({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <article className="preview-card">
      <span className="preview-icon">
        <ArrowIcon />
      </span>
      <div>
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </article>
  );
}

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [notes, setNotes] = useState("");
  const [result, setResult] = useState<FinalConsultationBundle | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [activeView, setActiveView] = useState<WorkspaceView>("overview");

  const fileInputId = useId();
  const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

  function handleSelectedFile(selectedFile: File | null) {
    setFile(selectedFile);

    if (selectedFile) {
      setError(null);
    }
  }

  function handleDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    setDragging(false);
    handleSelectedFile(event.dataTransfer.files?.[0] ?? null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!file) {
      setError("Choose a consultation recording before submitting.");
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("notes", notes);

    try {
      const response = await fetch(`${apiBaseUrl}/analyze`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        let errorPayload: ApiErrorPayload | null = null;

        try {
          errorPayload = (await response.json()) as ApiErrorPayload;
        } catch {
          errorPayload = null;
        }

        throw new Error(formatApiError(response.status, errorPayload));
      }

      const payload = (await response.json()) as FinalConsultationBundle;
      startTransition(() => {
        setResult(payload);
        setActiveView("overview");
      });
    } catch (requestError) {
      setResult(null);
      setError(
        requestError instanceof Error
          ? requestError.message
          : "The request failed.",
      );
    } finally {
      setLoading(false);
    }
  }

  const transcriptWordCount = result ? countWords(result.case.transcript) : 0;
  const totalIssues = result?.safety
    ? result.safety.warning_count + result.safety.blocker_count
    : 0;

  function renderActiveView() {
    if (!result) {
      return null;
    }

    switch (activeView) {
      case "overview":
        return (
          <div className="results-grid">
            <article className="result-hero">
              <p className="section-kicker">Chief complaint</p>
              <h3>{result.case.chief_complaint}</h3>
              <p className="lead-copy">{previewTranscript(result.case.transcript)}</p>
              <div className="pill-row">
                {result.case.duration ? (
                  <span className="soft-pill">Duration: {result.case.duration}</span>
                ) : null}
                {result.case.severity ? (
                  <span className="soft-pill">Severity: {result.case.severity}</span>
                ) : null}
                <span className="soft-pill">{transcriptWordCount} transcript words</span>
              </div>
              <details className="inline-details">
                <summary>View full transcript</summary>
                <p>{result.case.transcript}</p>
              </details>
            </article>

            <article className="result-card">
              <ListBlock
                title="Symptoms"
                items={result.case.symptoms}
                emptyText="No symptoms were extracted."
              />
            </article>

            <article className="result-card">
              <ListBlock
                title="Medications"
                items={result.case.medications}
                emptyText="No medications were captured."
              />
              <ListBlock
                title="Allergies"
                items={result.case.allergies}
                emptyText="No allergies were captured."
              />
            </article>

            <article className="result-card">
              <ListBlock
                title="History"
                items={result.case.history}
                emptyText="No history items were captured."
              />
            </article>

            <article className="result-card">
              <ListBlock
                title="Risk factors"
                items={result.case.risk_factors}
                emptyText="No risk factors were captured."
              />
            </article>
          </div>
        );

      case "differentials":
        return (
          <div className="stack-grid">
            {result.differentials.map((differential) => (
              <article className="result-card" key={differential.condition_name}>
                <div className="card-topline">
                  <div>
                    <p className="section-kicker">Differential</p>
                    <h3>{differential.condition_name}</h3>
                  </div>
                  <div className="pill-row">
                    {differential.urgency ? (
                      <span className="soft-pill">Urgency: {differential.urgency}</span>
                    ) : null}
                    <span className={`likelihood likelihood-${differential.likelihood}`}>
                      {differential.likelihood}
                    </span>
                  </div>
                </div>
                <p className="support-copy">{differential.reasoning}</p>
                <div className="section-grid">
                  <ListBlock
                    title="Supporting findings"
                    items={differential.supporting_findings}
                    emptyText="No supporting findings listed."
                  />
                  <ListBlock
                    title="Conflicting findings"
                    items={differential.conflicting_findings}
                    emptyText="No conflicts listed."
                  />
                  <ListBlock
                    title="Missing information"
                    items={differential.missing_information}
                    emptyText="No missing information listed."
                  />
                  <ListBlock
                    title="Recommended tests"
                    items={differential.recommended_tests}
                    emptyText="No tests recommended."
                  />
                </div>
              </article>
            ))}
          </div>
        );

      case "plan":
        return (
          <div className="stack-grid">
            <article className="result-hero result-hero-light">
              <p className="section-kicker">Care plan rationale</p>
              <h3>Recommended next steps</h3>
              <p className="lead-copy lead-copy-dark">{result.care_plan.rationale}</p>
            </article>

            <div className="section-grid">
              <article className="result-card">
                <ListBlock
                  title="Suggested tests"
                  items={result.care_plan.suggested_tests}
                  emptyText="No tests suggested."
                />
              </article>
              <article className="result-card">
                <ListBlock
                  title="Suggested referrals"
                  items={result.care_plan.suggested_referrals}
                  emptyText="No referrals suggested."
                />
              </article>
              <article className="result-card">
                <ListBlock
                  title="Follow-up"
                  items={result.care_plan.follow_up}
                  emptyText="No follow-up actions suggested."
                />
              </article>
              <article className="result-card">
                <ListBlock
                  title="Patient advice"
                  items={result.care_plan.patient_advice}
                  emptyText="No patient advice captured."
                />
              </article>
              <article className="result-card">
                <ListBlock
                  title="Red flags"
                  items={result.care_plan.red_flags}
                  emptyText="No red flags were returned."
                />
              </article>
            </div>
          </div>
        );

      case "documentation":
        return (
          <div className="stack-grid">
            <div className="section-grid">
              <article className="result-card">
                <p className="section-kicker">SOAP</p>
                <h3>Subjective</h3>
                <p>{result.soap_note.subjective}</p>
              </article>
              <article className="result-card">
                <p className="section-kicker">SOAP</p>
                <h3>Objective</h3>
                <p>{result.soap_note.objective}</p>
              </article>
              <article className="result-card">
                <p className="section-kicker">SOAP</p>
                <h3>Assessment</h3>
                <p>{result.soap_note.assessment}</p>
              </article>
              <article className="result-card">
                <p className="section-kicker">SOAP</p>
                <h3>Plan</h3>
                <p>{result.soap_note.plan}</p>
              </article>
            </div>

            <article className="result-card">
              <p className="section-kicker">Patient summary</p>
              <h3>What was discussed</h3>
              <p>{result.patient_summary.what_was_discussed}</p>
              <div className="section-grid">
                <ListBlock
                  title="Doctor may check next"
                  items={result.patient_summary.what_the_doctor_may_check_next}
                  emptyText="No follow-up checks were listed."
                />
                <ListBlock
                  title="What to do next"
                  items={result.patient_summary.what_you_should_do_next}
                  emptyText="No next steps were listed."
                />
                <ListBlock
                  title="When to get urgent help"
                  items={result.patient_summary.when_to_get_urgent_help}
                  emptyText="No urgent help guidance was listed."
                />
              </div>
            </article>
          </div>
        );

      case "safety":
        return result.safety ? (
          <div className="stack-grid">
            <article className={`result-hero result-hero-${result.safety.status}`}>
              <p className="section-kicker">Safety summary</p>
              <h3>{result.safety.red_flag_summary}</h3>
              <div className="pill-row">
                <span className="soft-pill">Warnings: {result.safety.warning_count}</span>
                <span className="soft-pill">Blockers: {result.safety.blocker_count}</span>
                <span className="soft-pill">
                  Evidence: {result.safety.uncertainty_assessment.evidence_level}
                </span>
              </div>
            </article>

            <div className="section-grid">
              <article className="result-card">
                <ListBlock
                  title="Detected red flags"
                  items={result.safety.red_flags.map((flag) => flag.title)}
                  emptyText="No red flags detected."
                />
              </article>
              <article className="result-card">
                <ListBlock
                  title="Safety issues"
                  items={result.safety.issues.map((issue) => issue.message)}
                  emptyText="No safety issues identified."
                />
              </article>
              <article className="result-card">
                <p className="section-kicker">Uncertainty assessment</p>
                <h3>{result.safety.uncertainty_assessment.summary}</h3>
                <div className="assessment-list">
                  <span>
                    Confidence alignment:
                    {" "}
                    <strong>{result.safety.uncertainty_assessment.confidence_alignment}</strong>
                  </span>
                  <span>
                    Explicit uncertainty:
                    {" "}
                    <strong>
                      {result.safety.uncertainty_assessment.explicit_uncertainty_present
                        ? "present"
                        : "missing"}
                    </strong>
                  </span>
                  <span>
                    Missing information documented:
                    {" "}
                    <strong>
                      {result.safety.uncertainty_assessment.missing_information_documented
                        ? "yes"
                        : "no"}
                    </strong>
                  </span>
                  <span>
                    High-likelihood support:
                    {" "}
                    <strong>
                      {result.safety.uncertainty_assessment
                        .supported_high_likelihood_differentials
                        ? "yes"
                        : "no"}
                    </strong>
                  </span>
                </div>
              </article>
            </div>
          </div>
        ) : (
          <article className="result-card">
            <p className="section-kicker">Safety</p>
            <h3>No safety payload was returned.</h3>
            <p>This run produced the consultation bundle without an attached safety report.</p>
          </article>
        );

      case "json":
        return (
          <article className="result-card">
            <p className="section-kicker">Raw response</p>
            <h3>Structured payload</h3>
            <details className="inline-details" open>
              <summary>Expand JSON</summary>
              <pre>{JSON.stringify(result, null, 2)}</pre>
            </details>
          </article>
        );

      default:
        return null;
    }
  }

  return (
    <main className="app-shell">
      <section className="workspace-shell">
        <header className="app-header">
          <div className="brand">
            <span className="brand-mark">
              <BrandMark />
            </span>
            <div className="brand-copy">
              <h1>Dr Assistant</h1>
              <p>Post-Consultation Review</p>
            </div>
          </div>

          <div className="trust-badge">
            <ShieldIcon />
            <span>Demo only. Not medical advice.</span>
          </div>
        </header>

        <section className="workspace-grid">
          <form className="intake-column" onSubmit={handleSubmit}>
            <div className="column-heading">
              <h2>Consultation Intake</h2>
              <p>Upload a recording and add optional notes</p>
            </div>

            <div className="intake-body">
              <div className="field-block">
                <p className="field-label">Recording</p>
                <label
                  className={`upload-dropzone ${dragging ? "upload-dragging" : ""} ${file ? "upload-ready" : ""}`}
                  htmlFor={fileInputId}
                  onDragOver={(event) => {
                    event.preventDefault();
                    setDragging(true);
                  }}
                  onDragLeave={(event) => {
                    event.preventDefault();
                    const nextTarget = event.relatedTarget;

                    if (!(nextTarget instanceof Node) || !event.currentTarget.contains(nextTarget)) {
                      setDragging(false);
                    }
                  }}
                  onDrop={handleDrop}
                >
                  <span className="dropzone-icon">
                    <UploadIcon />
                  </span>
                  <div className="dropzone-copy">
                    <h3>
                      {file ? file.name : "Drop consultation recording here"}
                    </h3>
                    <p>
                      {file
                        ? `${formatBytes(file.size)}${file.type ? ` | ${file.type}` : ""}`
                        : "or click to browse · MP3, WAV, M4A, MP4 up to 500 MB"}
                    </p>
                  </div>
                  <input
                    id={fileInputId}
                    className="sr-only"
                    type="file"
                    accept="audio/*,video/*"
                    onChange={(event) => {
                      handleSelectedFile(event.target.files?.[0] ?? null);
                    }}
                  />
                </label>
              </div>

              <div className="field-block">
                <label className="field-label" htmlFor="doctor-notes">
                  Clinician notes
                  <span className="field-optional"> (optional)</span>
                </label>
                <textarea
                  id="doctor-notes"
                  rows={7}
                  value={notes}
                  onChange={(event) => {
                    setNotes(event.target.value);
                  }}
                  placeholder="Add clinical context, prior findings, or specific questions for the review..."
                />
              </div>
            </div>

            <div className="intake-footer">
              <button className="submit-button" type="submit" disabled={loading}>
                <span>{loading ? "Running analysis..." : "Run Analysis"}</span>
                <ArrowIcon />
              </button>
              <p className="subtle-meta">Endpoint: {apiBaseUrl || "http://localhost:8000"}/analyze</p>
              {error ? <p className="error-banner">{error}</p> : null}
            </div>
          </form>

          <section className="review-column">
            {loading ? (
              <div className="loading-state">
                <div className="loading-icon-shell">
                  <span className="ready-icon">
                    <FileIcon />
                  </span>
                </div>
                <h2>Analyzing consultation</h2>
                <p>Running the intake through the structured review pipeline.</p>
                <div className="loading-list">
                  <div className="loading-card" />
                  <div className="loading-card" />
                  <div className="loading-card" />
                </div>
              </div>
            ) : result ? (
              <div className="review-results">
                <div className="review-header">
                  <div>
                    <h2>{result.case.chief_complaint}</h2>
                    <p>
                      Structured clinical review across overview, differentials, care
                      plan, documentation, safety, and raw JSON.
                    </p>
                  </div>
                  <div className="review-metadata">
                    <SafetyTone safety={result?.safety} />
                    <div className="pill-row">
                      <span className="soft-pill">{result.differentials.length} differentials</span>
                      <span className="soft-pill">{transcriptWordCount} words</span>
                      <span className="soft-pill">{totalIssues} issues</span>
                    </div>
                  </div>
                </div>

                <div className="view-tabs" aria-label="Result sections">
                  {VIEW_OPTIONS.map((view) => (
                    <button
                      key={view.id}
                      className={`view-tab ${activeView === view.id ? "view-tab-active" : ""}`}
                      type="button"
                      onClick={() => {
                        setActiveView(view.id);
                      }}
                      title={view.label}
                    >
                      {view.shortLabel}
                    </button>
                  ))}
                </div>

                <div className="results-stage">{renderActiveView()}</div>
              </div>
            ) : (
              <div className="empty-state">
                <span className="ready-icon">
                  <FileIcon />
                </span>
                <h2>Ready to review</h2>
                <p>
                  Upload a consultation recording and run the analysis to generate
                  a structured clinical review.
                </p>
                <div className="preview-list">
                  {SECTION_PREVIEWS.map((section) => (
                    <PreviewCard
                      key={section.title}
                      title={section.title}
                      description={section.description}
                    />
                  ))}
                </div>
              </div>
            )}
          </section>
        </section>
      </section>
    </main>
  );
}
