import { FormEvent, useEffect, useMemo, useState } from "react";
import { ApiError, api, waitForJob } from "./api";
import type {
  ConfigProfile,
  InterviewPackage,
  InterviewQuestion,
  InterviewReport,
  ProfileId,
  PublicConfig,
  Session,
  WorkflowJob,
} from "./types";

const SESSION_KEY = "interview-atelier-session";
const DEFAULT_FOCUS = "balanced company, role, technical, and behavioural coverage";
type WorkspaceView = "setup" | "research" | "fit" | "coaching";
type CoachingView = "questions" | "answers";
type IntakeErrors = {
  jobDescription?: string;
  candidateEvidence?: string;
};

export function recommendedQuestionIds(
  roleQuestions: InterviewQuestion[],
  hrQuestions: InterviewQuestion[],
  requestedCount: number,
): string[] {
  const count = Math.max(0, requestedCount);
  const hrReserve = count > 1 && hrQuestions.length > 0 ? 1 : 0;
  const initialRoleCount = Math.min(roleQuestions.length, count - hrReserve);
  const selected = roleQuestions.slice(0, initialRoleCount);

  const hrCount = Math.min(hrQuestions.length, count - selected.length);
  selected.push(...hrQuestions.slice(0, hrCount));

  const remaining = count - selected.length;
  if (remaining > 0) {
    selected.push(
      ...roleQuestions.slice(initialRoleCount, initialRoleCount + remaining),
    );
  }
  return selected.map((question) => question.questionId);
}

function scoreClass(score: number): string {
  if (score >= 80) return "score-good";
  if (score >= 55) return "score-mid";
  return "score-low";
}

function Metric({
  label,
  value,
  suffix = "%",
}: {
  label: string;
  value: number;
  suffix?: string;
}) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong className={scoreClass(suffix === "%" ? value : value * 20)}>
        {Number.isInteger(value) ? value : value.toFixed(1)}
        {suffix}
      </strong>
    </div>
  );
}

function AgentProgress({ job }: { job: WorkflowJob }) {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const percent = Math.round((job.completedSteps / Math.max(job.totalSteps, 1)) * 100);
  useEffect(() => {
    setElapsedSeconds(0);
    const timer = window.setInterval(() => {
      setElapsedSeconds((current) => current + 1);
    }, 1000);
    return () => window.clearInterval(timer);
  }, [job.jobId]);

  const elapsed = `${String(Math.floor(elapsedSeconds / 60)).padStart(2, "0")}:${String(
    elapsedSeconds % 60,
  ).padStart(2, "0")}`;

  return (
    <div className="activity-region">
      <aside
        className="agent-progress"
        role="status"
        aria-live="polite"
        aria-busy="true"
        aria-label={`Workflow in progress: ${job.message}`}
      >
        <div className="activity-mark" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <div className="activity-copy">
          <div className="activity-heading">
            <p className="eyebrow">Workflow in progress</p>
            <code>{elapsed}</code>
          </div>
          <strong>{job.message}</strong>
          <div
            className="progress-track"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={job.totalSteps}
            aria-valuenow={job.completedSteps}
          >
            <span style={{ width: `${percent}%` }} />
          </div>
          <small>
            {job.stage.replaceAll("_", " ")} · step {job.completedSteps} of{" "}
            {job.totalSteps}
          </small>
        </div>
      </aside>
    </div>
  );
}

function WorkspaceNav({
  active,
  plan,
  report,
  profile,
  onChange,
}: {
  active: WorkspaceView;
  plan: InterviewPackage;
  report: InterviewReport | null;
  profile: ConfigProfile;
  onChange: (view: WorkspaceView) => void;
}) {
  const items: Array<{
    id: WorkspaceView;
    code: string;
    label: string;
    meta: string;
  }> = [
    {
      id: "setup",
      code: "S",
      label: "Evidence & setup",
      meta: profile.label,
    },
    {
      id: "research",
      code: "E",
      label: "Company research",
      meta: `${plan.companyResearch.sources.length} sources`,
    },
    {
      id: "fit",
      code: "A",
      label: "Job fit",
      meta: `${Math.round(plan.jobFitMetrics.overallPercent)}% alignment`,
    },
    {
      id: "coaching",
      code: "D",
      label: "Interview coaching",
      meta: report
        ? `${report.answers.length} answers coached`
        : `${plan.questionQualityMetrics.totalQuestions} questions`,
    },
  ];

  return (
    <nav className="workspace-nav" aria-label="Interview workspace">
      <div role="tablist">
        {items.map((item) => (
          <button
            key={item.id}
            type="button"
            role="tab"
            aria-selected={active === item.id}
            className={active === item.id ? "active" : ""}
            onClick={() => onChange(item.id)}
          >
            <span aria-hidden="true">{item.code}</span>
            <strong>{item.label}</strong>
            <small>{item.meta}</small>
          </button>
        ))}
      </div>
    </nav>
  );
}

function AssessmentSummary({
  plan,
  session,
}: {
  plan: InterviewPackage;
  session: Session;
}) {
  const fit = plan.jobFitMetrics;
  const identifiers = [
    { label: "Role", value: plan.identity.roleTitle },
    { label: "Company", value: plan.identity.companyName },
    { label: "JD upload", value: session.jobDescriptionFilename },
    {
      label: "CV / profile",
      value: session.candidateFilename ?? "Candidate notes only",
    },
  ];
  const metrics = [
    { label: "Overall fit", value: fit.overallPercent },
    { label: "Must-have", value: fit.mustHavePercent },
    { label: "Evidence", value: fit.evidenceCoveragePercent },
    { label: "Confidence", value: fit.assessmentConfidencePercent },
  ];

  return (
    <section className="assessment-summary" aria-label="Assessment summary">
      <div className="assessment-context">
        <p>Assessment overview</p>
        <dl className="assessment-identifiers">
          {identifiers.map((item) => (
            <div key={item.label}>
              <dt>{item.label}</dt>
              <dd title={item.value}>{item.value}</dd>
            </div>
          ))}
        </dl>
      </div>
      <dl className="assessment-stats" aria-label="Job fit summary metrics">
        {metrics.map((metric) => (
          <div key={metric.label}>
            <dt>{metric.label}</dt>
            <dd className={scoreClass(metric.value)}>{Math.round(metric.value)}%</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function CompanyResearchView({ plan }: { plan: InterviewPackage }) {
  const research = plan.companyResearch;
  return (
    <>
      <section className="hero compact workspace-hero">
        <p className="eyebrow">Company research</p>
        <h1>Know the company before the room.</h1>
        <p>
          {research.summary ||
            `Research for ${plan.identity.companyName} is based on the supplied job description.`}
        </p>
      </section>

      <div className="research-layout">
        <section className="panel research-overview">
          <p className="eyebrow">Interview intelligence</p>
          <h2>Facts worth knowing</h2>
          {research.facts.length > 0 ? (
            <div className="fact-list">
              {research.facts.map((fact, index) => (
                <article key={`${fact.topic}-${index}`}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <div>
                    <h3>{fact.topic}</h3>
                    <p>{fact.finding}</p>
                    {fact.sourceIds.length > 0 && (
                      <small>Sources: {fact.sourceIds.join(", ")}</small>
                    )}
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <p className="empty-state">
              No verified company facts were available. Enable web research or provide a
              company hint for a richer result.
            </p>
          )}
        </section>

        <aside className="panel talking-points">
          <p className="eyebrow">Use in conversation</p>
          <h2>Talking points</h2>
          {research.interviewTalkingPoints.length > 0 ? (
            <ol>
              {research.interviewTalkingPoints.map((point) => (
                <li key={point}>{point}</li>
              ))}
            </ol>
          ) : (
            <p className="empty-state">
              No company-specific talking points were supported by the available evidence.
            </p>
          )}
        </aside>
      </div>

      <section className="source-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Evidence trail</p>
            <h2>Research sources</h2>
          </div>
          <span className="source-count">{research.sources.length} verified links</span>
        </div>
        {research.sources.length > 0 ? (
          <div className="source-grid">
            {research.sources.map((source) => (
              <a
                key={source.sourceId}
                className="source-card"
                href={source.url}
                target="_blank"
                rel="noreferrer"
              >
                <span>{source.sourceId}</span>
                <strong>{source.title}</strong>
                <p>{source.snippet}</p>
                <small>Open source ↗</small>
              </a>
            ))}
          </div>
        ) : (
          <div className="empty-panel">
            Web research was not used or no reliable public results were found.
          </div>
        )}
        {research.researchLimits.length > 0 && (
          <div className="research-limits">
            <strong>Research limits</strong>
            <ul>
              {research.researchLimits.map((limit) => (
                <li key={limit}>{limit}</li>
              ))}
            </ul>
          </div>
        )}
      </section>
    </>
  );
}

function JobFitView({ plan }: { plan: InterviewPackage }) {
  const analysis = plan.jdAnalysis;
  return (
    <>
      <section className="hero compact workspace-hero">
        <p className="eyebrow">Job fit assessment</p>
        <h1>Your evidence, mapped to the role.</h1>
        <p>{analysis.roleSummary}</p>
      </section>

      <div className="two-column fit-summary">
        <section className="panel">
          <p className="eyebrow">Your advantage</p>
          <h2>Strengths to lead with</h2>
          <ul className="check-list">
            {analysis.candidateStrengths.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
        <section className="panel">
          <p className="eyebrow">Preparation focus</p>
          <h2>Gaps to address</h2>
          <ul className="gap-list">
            {analysis.candidateGaps.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      </div>

      <section className="requirements-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Evidence matrix</p>
            <h2>Requirement-by-requirement assessment</h2>
          </div>
          <div className="fit-legend" aria-label="Assessment status legend">
            <span className="matched">Matched</span>
            <span className="partial">Partial</span>
            <span className="gap">Gap</span>
            <span className="unknown">Unknown</span>
          </div>
        </div>
        {analysis.requirementAssessments.length > 0 ? (
          <div className="requirement-list">
            {analysis.requirementAssessments.map((assessment, index) => (
              <article key={`${assessment.requirement}-${index}`}>
                <span className={`status-mark ${assessment.status}`} />
                <div>
                  <small>{assessment.category.replaceAll("_", " ")}</small>
                  <h3>{assessment.requirement}</h3>
                  <p>
                    {assessment.evidence ||
                      "No direct candidate evidence was found in the supplied profile."}
                  </p>
                </div>
                <div className={`status-label ${assessment.status}`}>
                  {assessment.status}
                  <small>{Math.round(assessment.confidence * 100)}% confidence</small>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-panel">No requirement assessments were generated.</div>
        )}
      </section>

      <section className="role-details panel">
        <div>
          <p className="eyebrow">Role signals</p>
          <h2>What the job emphasizes</h2>
        </div>
        <div className="detail-columns">
          <div>
            <h3>Must-have skills</h3>
            <div className="chip-list">
              {analysis.mustHaveSkills.map((skill) => (
                <span key={skill}>{skill}</span>
              ))}
            </div>
          </div>
          <div>
            <h3>Likely challenges</h3>
            <ul>
              {analysis.likelyChallenges.map((challenge) => (
                <li key={challenge}>{challenge}</li>
              ))}
            </ul>
          </div>
        </div>
      </section>
    </>
  );
}

function QuestionCard({
  question,
  selected,
  disabled,
  onToggle,
}: {
  question: InterviewQuestion;
  selected: boolean;
  disabled: boolean;
  onToggle: () => void;
}) {
  return (
    <article className={`question-card ${selected ? "selected" : ""}`}>
      <label>
        <input
          type="checkbox"
          checked={selected}
          disabled={disabled}
          onChange={onToggle}
        />
        <span className="question-id">{question.questionId}</span>
        <span className="question-category">{question.category}</span>
      </label>
      <h3>{question.question}</h3>
      <p>{question.rationale}</p>
      {question.strongAnswerSignals.length > 0 && (
        <details>
          <summary>What a strong answer covers</summary>
          <ul>
            {question.strongAnswerSignals.map((signal) => (
              <li key={signal}>{signal}</li>
            ))}
          </ul>
        </details>
      )}
    </article>
  );
}

function CoachingQuestionsView({
  plan,
  profile,
  selected,
  busy,
  reportReady,
  onToggle,
  onSelectRecommended,
  onGenerate,
}: {
  plan: InterviewPackage;
  profile: ConfigProfile;
  selected: Set<string>;
  busy: boolean;
  reportReady: boolean;
  onToggle: (id: string) => void;
  onSelectRecommended: () => void;
  onGenerate: () => void;
}) {
  const questions = [
    ...plan.interviewPlan.roleCompanyQuestions,
    ...plan.interviewPlan.hrQuestions,
  ];

  return (
    <>
      <section className="hero compact workspace-hero">
        <p className="eyebrow">Interview coaching</p>
        <h1>Practice what matters most.</h1>
        <p>
          Review the generated bank for {plan.identity.roleTitle}, then choose the
          questions where grounded answer coaching will help most.
        </p>
      </section>

      <section className="question-section workspace-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Practice set</p>
            <h2>Choose answers to coach</h2>
            <p>
              Select up to {profile.maxAnswerCount}. A focused set is faster and usually
              more useful for a demonstration.
            </p>
          </div>
          <div className="selection-tools">
            <button className="button ghost" type="button" onClick={onSelectRecommended}>
              Recommended {profile.defaultAnswerCount}
            </button>
            <span>
              <strong>{selected.size}</strong> / {profile.maxAnswerCount}
            </span>
          </div>
        </div>
        <div className="question-grid">
          {questions.map((question) => (
            <QuestionCard
              key={question.questionId}
              question={question}
              selected={selected.has(question.questionId)}
              disabled={!selected.has(question.questionId) && selected.size >= profile.maxAnswerCount}
              onToggle={() => onToggle(question.questionId)}
            />
          ))}
        </div>
        <div className="sticky-action">
          <div>
            <strong>{selected.size} questions selected</strong>
            <span>
              {reportReady
                ? "A new run will replace the current coached-answer report."
                : "The answer and evaluator agents will use only your evidence."}
            </span>
          </div>
          <button
            className="button primary"
            type="button"
            disabled={busy || selected.size === 0}
            onClick={onGenerate}
          >
            {reportReady ? "Re-coach selected answers" : "Draft & coach answers"}
          </button>
        </div>
      </section>
    </>
  );
}

function CoachingSubnav({
  active,
  answerCount,
  onChange,
}: {
  active: CoachingView;
  answerCount: number;
  onChange: (view: CoachingView) => void;
}) {
  return (
    <div className="coaching-subnav" role="tablist" aria-label="Coaching content">
      <button
        type="button"
        role="tab"
        aria-selected={active === "questions"}
        className={active === "questions" ? "active" : ""}
        onClick={() => onChange("questions")}
      >
        Question bank
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={active === "answers"}
        className={active === "answers" ? "active" : ""}
        onClick={() => onChange("answers")}
      >
        Coached answers <span>{answerCount}</span>
      </button>
    </div>
  );
}

function ReportView({
  report,
  sessionId,
}: {
  report: InterviewReport;
  sessionId: string;
}) {
  const questions = new Map(
    [
      ...report.package.interviewPlan.roleCompanyQuestions,
      ...report.package.interviewPlan.hrQuestions,
    ].map((question) => [question.questionId, question]),
  );
  const evaluations = new Map(
    report.evaluations.map((evaluation) => [evaluation.questionId, evaluation]),
  );
  const metrics = report.answerQualityMetrics;

  return (
    <>
      <section className="hero compact report-hero">
        <p className="eyebrow">Coaching complete</p>
        <h1>Your interview playbook is ready.</h1>
        <p>
          Grounded drafts, evaluator notes, and evidence gaps for{" "}
          {report.package.identity.roleTitle} at {report.package.identity.companyName}.
        </p>
        <div className="download-row">
          <a className="button primary" href={api.downloadUrl(sessionId, "md")}>
            Download Markdown
          </a>
          <a className="button ghost" href={api.downloadUrl(sessionId, "json")}>
            Download JSON
          </a>
        </div>
      </section>

      <section className="metrics-grid report-metrics">
        <Metric label="Average answer" value={metrics.averageScore} suffix="/5" />
        <Metric label="Passing rate" value={metrics.passingRatePercent} />
        <Metric label="Evidence usage" value={metrics.evidenceUsagePercent} />
        <Metric label="Needs attention" value={metrics.answersNeedingImprovement} suffix="" />
      </section>

      <section className="answer-list">
        {report.answers.map((answer, index) => {
          const question = questions.get(answer.questionId);
          const evaluation = evaluations.get(answer.questionId);
          return (
            <article className="answer-card" key={answer.questionId}>
              <div className="answer-number">{String(index + 1).padStart(2, "0")}</div>
              <div className="answer-content">
                <div className="answer-heading">
                  <div>
                    <p className="eyebrow">
                      {answer.questionId} · {question?.category}
                    </p>
                    <h2>{question?.question ?? answer.questionId}</h2>
                  </div>
                  {evaluation && (
                    <span className={`score-pill score-${evaluation.score}`}>
                      {evaluation.score}/5
                    </span>
                  )}
                </div>
                <div className="draft">
                  <p>{answer.answer}</p>
                </div>
                {evaluation && (
                  <div className="coach-grid">
                    <div>
                      <h3>What works</h3>
                      <ul className="check-list">
                        {evaluation.strengths.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <h3>Sharpen next</h3>
                      <ul className="gap-list">
                        {evaluation.improvementInstructions.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
                {answer.missingEvidence.length > 0 && (
                  <p className="evidence-note">
                    <strong>Evidence to add:</strong> {answer.missingEvidence.join("; ")}
                  </p>
                )}
              </div>
            </article>
          );
        })}
      </section>
    </>
  );
}

export default function App() {
  const [config, setConfig] = useState<PublicConfig | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [plan, setPlan] = useState<InterviewPackage | null>(null);
  const [report, setReport] = useState<InterviewReport | null>(null);
  const [job, setJob] = useState<WorkflowJob | null>(null);
  const [error, setError] = useState("");
  const [intakeErrors, setIntakeErrors] = useState<IntakeErrors>({});
  const [restoring, setRestoring] = useState(true);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [workspaceView, setWorkspaceView] = useState<WorkspaceView>("research");
  const [coachingView, setCoachingView] = useState<CoachingView>("questions");

  const [profile, setProfile] = useState<ProfileId>("demo");
  const [jobDescription, setJobDescription] = useState<File | null>(null);
  const [candidateFile, setCandidateFile] = useState<File | null>(null);
  const [candidateNotes, setCandidateNotes] = useState("");
  const [companyHint, setCompanyHint] = useState("");
  const [focus, setFocus] = useState(DEFAULT_FOCUS);
  const [webResearch, setWebResearch] = useState(false);

  const busy = job?.state === "queued" || job?.state === "running";
  const intakeErrorMessages = Object.values(intakeErrors).filter(
    (message): message is string => Boolean(message),
  );
  const activeProfile = useMemo(
    () => config?.profiles.find((item) => item.id === (session?.profile ?? profile)),
    [config, profile, session?.profile],
  );

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const loadedConfig = await api.config();
        if (!active) return;
        setConfig(loadedConfig);
        setProfile(loadedConfig.defaultProfile);
        const saved = sessionStorage.getItem(SESSION_KEY);
        if (!saved) return;
        const restored = await api.session(saved);
        if (!active) return;
        setSession(restored);
        setProfile(restored.profile);
        if (restored.hasPlan) {
          const loadedPlan = await api.plan(saved);
          if (!active) return;
          setPlan(loadedPlan);
          chooseRecommended(loadedPlan, restored.profile, loadedConfig);
          setWorkspaceView("research");
        }
        if (restored.hasReport) {
          const loadedReport = await api.report(saved);
          if (active) {
            setReport(loadedReport);
            setWorkspaceView("coaching");
            setCoachingView("answers");
          }
        }
      } catch (caught) {
        sessionStorage.removeItem(SESSION_KEY);
        if (caught instanceof ApiError && caught.status !== 404 && caught.status !== 410) {
          setError(caught.message);
        }
      } finally {
        if (active) setRestoring(false);
      }
    };
    void load();
    return () => {
      active = false;
    };
  }, []);

  const chooseRecommended = (
    sourcePlan = plan,
    profileId = session?.profile ?? profile,
    sourceConfig = config,
  ) => {
    if (!sourcePlan || !sourceConfig) return;
    const count =
      sourceConfig.profiles.find((item) => item.id === profileId)?.defaultAnswerCount ?? 2;
    const roleQuestions = sourcePlan.interviewPlan.roleCompanyQuestions;
    const hrQuestions = sourcePlan.interviewPlan.hrQuestions;
    setSelected(new Set(recommendedQuestionIds(roleQuestions, hrQuestions, count)));
  };

  const clearIntakeError = (field: keyof IntakeErrors) => {
    setIntakeErrors((current) => {
      const next = { ...current };
      delete next[field];
      if (!Object.values(next).some(Boolean)) {
        setError("");
      }
      return next;
    });
  };

  const buildPlan = async (created: Session) => {
    const started = await api.startPlan(created.sessionId);
    await waitForJob(started, setJob);
    const completedPlan = await api.plan(created.sessionId);
    setPlan(completedPlan);
    setReport(null);
    chooseRecommended(completedPlan, created.profile);
    setWorkspaceView("research");
    setCoachingView("questions");
    setSession(await api.session(created.sessionId));
    setJob(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const begin = async (event?: FormEvent, example = false) => {
    event?.preventDefault();
    const previousSessionId = session?.sessionId;
    let created: Session | null = null;
    setError("");
    setIntakeErrors({});
    setJob(null);
    if (!example) {
      const nextErrors: IntakeErrors = {};
      if (!jobDescription) {
        nextErrors.jobDescription = "Choose a job description file.";
      }
      if (!candidateFile && !candidateNotes.trim()) {
        nextErrors.candidateEvidence =
          "Add a CV/profile file or candidate evidence notes.";
      }
      if (Object.keys(nextErrors).length > 0) {
        setIntakeErrors(nextErrors);
        setError("Complete the highlighted evidence fields before building the plan.");
        return;
      }
    }
    try {
      if (example) {
        created = await api.createExample(profile, companyHint, focus);
      } else {
        const form = new FormData();
        form.append("job_description", jobDescription!);
        if (candidateFile) form.append("candidate_profile", candidateFile);
        form.append("candidate_notes", candidateNotes);
        form.append("company_hint", companyHint);
        form.append("interview_focus", focus);
        form.append("web_research", String(webResearch));
        form.append("profile", profile);
        created = await api.createSession(form);
      }
      await buildPlan(created);
      setProfile(created.profile);
      sessionStorage.setItem(SESSION_KEY, created.sessionId);
      if (previousSessionId && previousSessionId !== created.sessionId) {
        try {
          await api.deleteSession(previousSessionId);
        } catch {
          // The replacement session is ready; the expired local session can age out.
        }
      }
    } catch (caught) {
      if (created && created.sessionId !== previousSessionId) {
        try {
          await api.deleteSession(created.sessionId);
        } catch {
          // Failed temporary sessions expire automatically.
        }
      }
      setJob(null);
      setError(caught instanceof Error ? caught.message : "Could not start the workflow.");
    }
  };

  const generateAnswers = async () => {
    if (!session || selected.size === 0) return;
    setError("");
    try {
      const started = await api.startAnswers(session.sessionId, [...selected]);
      await waitForJob(started, setJob);
      const completedReport = await api.report(session.sessionId);
      setReport(completedReport);
      setSession(await api.session(session.sessionId));
      setWorkspaceView("coaching");
      setCoachingView("answers");
      setJob(null);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (caught) {
      setJob(null);
      setError(caught instanceof Error ? caught.message : "Could not coach the answers.");
    }
  };

  const retryPlan = async () => {
    if (!session) return;
    setError("");
    try {
      await buildPlan(session);
    } catch (caught) {
      setJob(null);
      setError(caught instanceof Error ? caught.message : "Could not rebuild the plan.");
    }
  };

  const startOver = async () => {
    const currentId = session?.sessionId;
    setSession(null);
    setPlan(null);
    setReport(null);
    setJob(null);
    setSelected(new Set());
    setWorkspaceView("research");
    setCoachingView("questions");
    setError("");
    setIntakeErrors({});
    sessionStorage.removeItem(SESSION_KEY);
    if (currentId) {
      try {
        await api.deleteSession(currentId);
      } catch {
        // Local UI state is already safely cleared.
      }
    }
  };

  const toggleQuestion = (id: string) => {
    const maximum = activeProfile?.maxAnswerCount ?? 1;
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else if (next.size < maximum) next.add(id);
      return next;
    });
  };

  if (restoring) {
    return (
      <main className="loading-screen">
        <div className="brand-mark">IA</div>
        <p>Opening your interview workspace…</p>
      </main>
    );
  }

  return (
    <>
      <header className="topbar">
        <a className="brand" href="/" onClick={(event) => event.preventDefault()}>
          <span className="brand-mark">IA</span>
          <span>
            Interview <em>Atelier</em>
          </span>
        </a>
        <div className="runtime">
          <span className="status-dot" />
          Private local models
          {session && (
            <button type="button" onClick={() => void startOver()}>
              Start over
            </button>
          )}
        </div>
      </header>

      <main>
        {error && (
          <div className="error-banner" role="alert" tabIndex={0}>
            <strong>Something needs attention.</strong>
            <span>{error}</span>
            {intakeErrorMessages.length > 1 && (
              <ul>
                {intakeErrorMessages.map((message) => (
                  <li key={message}>{message}</li>
                ))}
              </ul>
            )}
            {session && !plan && !busy && (
              <button
                className="retry-link"
                type="button"
                onClick={() => void retryPlan()}
              >
                Retry with the same files
              </button>
            )}
            <button
              className="dismiss-error"
              type="button"
              aria-label="Dismiss error"
              onClick={() => setError("")}
            >
              ×
            </button>
          </div>
        )}
        {busy && job && <AgentProgress job={job} />}

        {session && plan && activeProfile && (
          <WorkspaceNav
            active={workspaceView}
            plan={plan}
            report={report}
            profile={activeProfile}
            onChange={(view) => {
              setWorkspaceView(view);
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
          />
        )}

        {(!session || (plan && workspaceView === "setup")) && (
          <section
            className="setup-workspace"
            role={session ? "tabpanel" : undefined}
            aria-label={session ? "Evidence and setup" : undefined}
          >
            <section className="hero landing-hero">
              <div className="hero-statement">
                <p className="eyebrow">Private interview preparation</p>
                <h1>
                  Prepare with evidence, <em>not guesswork.</em>
                </h1>
                <p className="hero-copy">
                  Turn a job description and your real experience into researched
                  questions, grounded answers, and candid coaching.
                </p>
              </div>
              <div className="evidence-trace" aria-label="How evidence informs the plan">
                <div className="trace-heading">
                  <span>Decision trace</span>
                  <strong>What shapes your plan</strong>
                </div>
                <div className="trace-row">
                  <code>E01</code>
                  <div>
                    <strong>Role requirements</strong>
                    <span>Extracted from the job description</span>
                  </div>
                </div>
                <div className="trace-row">
                  <code>E02</code>
                  <div>
                    <strong>Candidate evidence</strong>
                    <span>Mapped from your CV and verified notes</span>
                  </div>
                </div>
                <div className="trace-row decision">
                  <code>D01</code>
                  <div>
                    <strong>Preparation priorities</strong>
                    <span>Questions and coaching tied back to evidence</span>
                  </div>
                </div>
              </div>
            </section>

            <div className="agent-strip" aria-label="Workflow stages">
              {["Research", "Analyse", "Question", "Answer", "Evaluate"].map(
                (stage, index) => (
                  <span key={stage}>
                    <b>{String(index + 1).padStart(2, "0")}</b> {stage}
                  </span>
                ),
              )}
            </div>

            <form className="intake" onSubmit={(event) => void begin(event)}>
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Create your preparation brief</p>
                  <h2>Add the role and the evidence you can stand behind.</h2>
                </div>
                <button
                  className="button text-button"
                  type="button"
                  disabled={busy || !config}
                  onClick={() => void begin(undefined, true)}
                >
                  Try with sample files →
                </button>
              </div>

              <div className="upload-grid">
                <label
                  className={`file-drop ${jobDescription ? "has-file" : ""} ${
                    intakeErrors.jobDescription ? "has-error" : ""
                  }`}
                >
                  <span className="file-icon">JD</span>
                  <strong>{jobDescription?.name ?? "Job description"}</strong>
                  <small>PDF, DOCX, TXT or Markdown · required</small>
                  {intakeErrors.jobDescription && (
                    <small className="field-error" id="job-description-error">
                      {intakeErrors.jobDescription}
                    </small>
                  )}
                  <input
                    type="file"
                    accept=".pdf,.docx,.txt,.md"
                    aria-invalid={Boolean(intakeErrors.jobDescription)}
                    aria-describedby={
                      intakeErrors.jobDescription ? "job-description-error" : undefined
                    }
                    onChange={(event) => {
                      setJobDescription(event.target.files?.[0] ?? null);
                      clearIntakeError("jobDescription");
                    }}
                  />
                </label>
                <label
                  className={`file-drop ${candidateFile ? "has-file" : ""} ${
                    intakeErrors.candidateEvidence ? "has-error" : ""
                  }`}
                >
                  <span className="file-icon">CV</span>
                  <strong>{candidateFile?.name ?? "CV or candidate profile"}</strong>
                  <small>Optional when notes are supplied</small>
                  {intakeErrors.candidateEvidence && (
                    <small className="field-error" id="candidate-evidence-error">
                      {intakeErrors.candidateEvidence}
                    </small>
                  )}
                  <input
                    type="file"
                    accept=".pdf,.docx,.txt,.md"
                    aria-invalid={Boolean(intakeErrors.candidateEvidence)}
                    aria-describedby={
                      intakeErrors.candidateEvidence
                        ? "candidate-evidence-error"
                        : undefined
                    }
                    onChange={(event) => {
                      setCandidateFile(event.target.files?.[0] ?? null);
                      clearIntakeError("candidateEvidence");
                    }}
                  />
                </label>
              </div>

              <label className="field">
                <span>Candidate evidence or achievement notes</span>
                <textarea
                  rows={4}
                  value={candidateNotes}
                  aria-invalid={Boolean(intakeErrors.candidateEvidence)}
                  aria-describedby={
                    intakeErrors.candidateEvidence ? "candidate-evidence-error" : undefined
                  }
                  onChange={(event) => {
                    setCandidateNotes(event.target.value);
                    if (event.target.value.trim()) {
                      clearIntakeError("candidateEvidence");
                    }
                  }}
                  placeholder="Add verified projects, outcomes, metrics, or context not included in your CV."
                />
              </label>

              <div className="form-grid">
                <label className="field">
                  <span>Company hint <small>optional</small></span>
                  <input
                    value={companyHint}
                    onChange={(event) => setCompanyHint(event.target.value)}
                    placeholder="e.g. Anthropic"
                  />
                </label>
                <label className="field">
                  <span>Interview emphasis</span>
                  <input value={focus} onChange={(event) => setFocus(event.target.value)} />
                </label>
              </div>

              <fieldset className="profile-picker">
                <legend>Choose the pace</legend>
                <div>
                  {config?.profiles.map((item) => (
                    <label key={item.id} className={profile === item.id ? "active" : ""}>
                      <input
                        type="radio"
                        name="profile"
                        value={item.id}
                        checked={profile === item.id}
                        onChange={() => setProfile(item.id)}
                      />
                      <span>
                        <b>{item.label}</b>
                        <small>{item.description}</small>
                        <i>{item.model}</i>
                      </span>
                    </label>
                  ))}
                </div>
              </fieldset>

              <div className="submit-row">
                <label className="toggle">
                  <input
                    type="checkbox"
                    checked={webResearch}
                    onChange={(event) => setWebResearch(event.target.checked)}
                  />
                  <span />
                  Search current public company information
                </label>
                <button className="button primary" disabled={busy || !config}>
                  {session && plan ? "Build new interview plan" : "Build interview plan"}
                </button>
              </div>
              <p className="privacy-note">
                Model inference stays on this machine. Enable web research only when you
                want the company name sent to public search.
              </p>
            </form>
          </section>
        )}

        {session && plan && activeProfile && workspaceView !== "setup" && (
          <>
            <AssessmentSummary plan={plan} session={session} />

            {workspaceView === "research" && <CompanyResearchView plan={plan} />}

            {workspaceView === "fit" && <JobFitView plan={plan} />}

            {workspaceView === "coaching" && (
              <>
                {report && (
                  <CoachingSubnav
                    active={coachingView}
                    answerCount={report.answers.length}
                    onChange={setCoachingView}
                  />
                )}
                {(!report || coachingView === "questions") && (
                  <CoachingQuestionsView
                    plan={plan}
                    profile={activeProfile}
                    selected={selected}
                    busy={busy}
                    reportReady={report !== null}
                    onToggle={toggleQuestion}
                    onSelectRecommended={() => chooseRecommended()}
                    onGenerate={() => void generateAnswers()}
                  />
                )}
                {report && coachingView === "answers" && (
                  <ReportView report={report} sessionId={session.sessionId} />
                )}
              </>
            )}
          </>
        )}
      </main>

      <footer>
        <span>
          Interview Atelier · v{config?.appVersion ?? "0.2.3"} · build{" "}
          <code>{config?.buildTag ?? "unknown"}</code>
        </span>
        <span>Preparation indicators are guidance, not hiring predictions.</span>
      </footer>
    </>
  );
}
