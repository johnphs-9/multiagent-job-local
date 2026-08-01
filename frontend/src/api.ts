import type {
  InterviewPackage,
  InterviewReport,
  PublicConfig,
  Session,
  WorkflowJob,
} from "./types";

const API = "/api/v1";

export class ApiError extends Error {
  status: number;
  retryable: boolean;

  constructor(message: string, status: number, retryable = false) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.retryable = retryable;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, init);
  if (!response.ok) {
    let message = `Request failed (${response.status}).`;
    let retryable = response.status >= 500;
    try {
      const payload = await response.json();
      message = payload.error?.message ?? payload.detail ?? message;
      retryable = payload.error?.retryable ?? retryable;
    } catch {
      // Keep the safe status-based fallback.
    }
    throw new ApiError(message, response.status, retryable);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  config: () => request<PublicConfig>("/config"),
  session: (sessionId: string) => request<Session>(`/sessions/${sessionId}`),
  deleteSession: (sessionId: string) =>
    request<void>(`/sessions/${sessionId}`, { method: "DELETE" }),
  createExample: (profile: string, companyHint: string, interviewFocus: string) =>
    request<Session>("/sessions/examples", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        profile,
        company_hint: companyHint,
        interview_focus: interviewFocus,
        web_research: false,
      }),
    }),
  createSession: (form: FormData) =>
    request<Session>("/sessions", { method: "POST", body: form }),
  startPlan: (sessionId: string) =>
    request<WorkflowJob>(`/sessions/${sessionId}/plan-jobs`, {
      method: "POST",
      headers: { "Idempotency-Key": crypto.randomUUID() },
    }),
  plan: (sessionId: string) =>
    request<InterviewPackage>(`/sessions/${sessionId}/plan`),
  startAnswers: (sessionId: string, selectedQuestionIds: string[]) =>
    request<WorkflowJob>(`/sessions/${sessionId}/answer-jobs`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Idempotency-Key": crypto.randomUUID(),
      },
      body: JSON.stringify({ selected_question_ids: selectedQuestionIds }),
    }),
  job: (jobId: string) => request<WorkflowJob>(`/jobs/${jobId}`),
  cancelJob: (jobId: string) =>
    request<WorkflowJob>(`/jobs/${jobId}/cancel`, { method: "POST" }),
  report: (sessionId: string) =>
    request<InterviewReport>(`/sessions/${sessionId}/report`),
  downloadUrl: (sessionId: string, format: "md" | "json") =>
    `${API}/sessions/${sessionId}/downloads/report.${format}`,
};

export async function waitForJob(
  initial: WorkflowJob,
  onProgress: (job: WorkflowJob) => void,
): Promise<WorkflowJob> {
  let job = initial;
  let polls = 0;
  onProgress(job);
  while (job.state === "queued" || job.state === "running") {
    await new Promise((resolve) => window.setTimeout(resolve, polls < 10 ? 1000 : 2200));
    job = await api.job(job.jobId);
    onProgress(job);
    polls += 1;
  }
  if (job.state !== "succeeded") {
    throw new ApiError(job.message || "The workflow did not complete.", 500, job.retryable);
  }
  return job;
}
