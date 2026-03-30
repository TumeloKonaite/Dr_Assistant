import { FormEvent, startTransition, useState } from "react";

type Likelihood = "high" | "moderate" | "lower";
type SafetyStatus = "clear" | "warning" | "blocked";

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

function ListBlock({
  title,
  items,
}: {
  title: string;
  items: string[];
}) {
  if (!items.length) {
    return null;
  }

  return (
    <section className="list-block">
      <h3>{title}</h3>
      <ul>
        {items.map((item) => (
          <li key={`${title}-${item}`}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

function SafetyTone({ safety }: { safety?: SafetyReport | null }) {
  if (!safety) {
    return <span className="status status-muted">No safety report</span>;
  }

  return (
    <span className={`status status-${safety.status}`}>
      Safety {safety.status}
    </span>
  );
}

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [notes, setNotes] = useState("");
  const [result, setResult] = useState<FinalConsultationBundle | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

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

  return (
    <main className="app-shell">
      <section className="hero">
        <div className="eyebrow">PR9 Interface Preview</div>
        <h1>Clinical review, surfaced beyond the CLI.</h1>
        <p className="hero-copy">
          Upload a consultation recording, add doctor notes, and inspect the
          structured <code>FinalConsultationBundle</code> returned by the
          canonical pipeline.
        </p>
      </section>

      <section className="workspace">
        <form className="panel input-panel" onSubmit={handleSubmit}>
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Input</p>
              <h2>Analyze consultation</h2>
            </div>
            <div className="endpoint-chip">
              POST <code>{apiBaseUrl || "http://localhost:8000"}/analyze</code>
            </div>
          </div>

          <label className="field">
            <span>Consultation file</span>
            <input
              type="file"
              accept="audio/*,video/*"
              onChange={(event) => {
                setFile(event.target.files?.[0] ?? null);
              }}
            />
          </label>

          <label className="field">
            <span>Doctor notes</span>
            <textarea
              rows={8}
              value={notes}
              onChange={(event) => {
                setNotes(event.target.value);
              }}
              placeholder="Optional context from the clinician."
            />
          </label>

          <button className="submit-button" type="submit" disabled={loading}>
            {loading ? "Running pipeline..." : "Run analysis"}
          </button>

          {error ? <p className="error-banner">{error}</p> : null}
        </form>

        <section className="panel results-panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Output</p>
              <h2>Consultation bundle</h2>
            </div>
            <SafetyTone safety={result?.safety} />
          </div>

          {result ? (
            <div className="results-grid">
              <article className="result-card emphasis-card">
                <p className="card-label">Case</p>
                <h3>{result.case.chief_complaint}</h3>
                <p className="card-copy">{result.case.transcript}</p>
                <div className="meta-row">
                  {result.case.duration ? (
                    <span>Duration: {result.case.duration}</span>
                  ) : null}
                  {result.case.severity ? (
                    <span>Severity: {result.case.severity}</span>
                  ) : null}
                </div>
                <ListBlock title="Symptoms" items={result.case.symptoms} />
              </article>

              <article className="result-card">
                <p className="card-label">Differentials</p>
                <div className="differential-stack">
                  {result.differentials.map((differential) => (
                    <section
                      className="differential-card"
                      key={differential.condition_name}
                    >
                      <div className="differential-head">
                        <h3>{differential.condition_name}</h3>
                        <span className={`likelihood likelihood-${differential.likelihood}`}>
                          {differential.likelihood}
                        </span>
                      </div>
                      <p>{differential.reasoning}</p>
                      <ListBlock
                        title="Supporting findings"
                        items={differential.supporting_findings}
                      />
                      <ListBlock
                        title="Missing information"
                        items={differential.missing_information}
                      />
                      <ListBlock
                        title="Recommended tests"
                        items={differential.recommended_tests}
                      />
                    </section>
                  ))}
                </div>
              </article>

              <article className="result-card">
                <p className="card-label">Care plan</p>
                <p className="card-copy">{result.care_plan.rationale}</p>
                <ListBlock
                  title="Suggested tests"
                  items={result.care_plan.suggested_tests}
                />
                <ListBlock
                  title="Suggested referrals"
                  items={result.care_plan.suggested_referrals}
                />
                <ListBlock title="Follow-up" items={result.care_plan.follow_up} />
                <ListBlock title="Red flags" items={result.care_plan.red_flags} />
                <ListBlock
                  title="Patient advice"
                  items={result.care_plan.patient_advice}
                />
              </article>

              <article className="result-card">
                <p className="card-label">Documentation</p>
                <div className="note-block">
                  <h3>SOAP note</h3>
                  <p><strong>Subjective:</strong> {result.soap_note.subjective}</p>
                  <p><strong>Objective:</strong> {result.soap_note.objective}</p>
                  <p><strong>Assessment:</strong> {result.soap_note.assessment}</p>
                  <p><strong>Plan:</strong> {result.soap_note.plan}</p>
                </div>
                <div className="note-block">
                  <h3>Patient summary</h3>
                  <p>{result.patient_summary.what_was_discussed}</p>
                  <ListBlock
                    title="What the doctor may check next"
                    items={result.patient_summary.what_the_doctor_may_check_next}
                  />
                  <ListBlock
                    title="What you should do next"
                    items={result.patient_summary.what_you_should_do_next}
                  />
                  <ListBlock
                    title="When to get urgent help"
                    items={result.patient_summary.when_to_get_urgent_help}
                  />
                </div>
              </article>

              {result.safety ? (
                <article className="result-card">
                  <p className="card-label">Safety</p>
                  <p className="card-copy">{result.safety.red_flag_summary}</p>
                  <div className="meta-row">
                    <span>Warnings: {result.safety.warning_count}</span>
                    <span>Blockers: {result.safety.blocker_count}</span>
                  </div>
                  <ListBlock
                    title="Detected red flags"
                    items={result.safety.red_flags.map((flag) => flag.title)}
                  />
                  <ListBlock
                    title="Safety issues"
                    items={result.safety.issues.map((issue) => issue.message)}
                  />
                </article>
              ) : null}

              <article className="result-card raw-card">
                <p className="card-label">Raw JSON</p>
                <pre>{JSON.stringify(result, null, 2)}</pre>
              </article>
            </div>
          ) : (
            <div className="empty-state">
              <p>No bundle yet.</p>
              <span>
                Submit a file and optional notes to inspect the API response.
              </span>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}
