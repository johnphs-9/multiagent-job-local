"""Thread-safe ephemeral sessions and bounded background jobs."""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

from interview_local.schemas import InterviewPackage, InterviewReport

JobState = Literal["queued", "running", "succeeded", "failed", "cancelled"]
JobType = Literal["plan", "answers"]
JobOperation = Callable[
    ["SessionRecord", Callable[[str, str, int, int], None], threading.Event], None
]
LOGGER = logging.getLogger(__name__)


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def payload_digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class SessionRecord:
    session_id: str
    profile: str
    job_description: str
    candidate_profile: str
    job_description_filename: str
    candidate_filename: str | None
    company_hint: str
    interview_focus: str
    web_research: bool
    created_at: str = field(default_factory=utc_now)
    last_access_monotonic: float = field(default_factory=time.monotonic)
    active_job_id: str | None = None
    package: InterviewPackage | None = None
    report: InterviewReport | None = None


@dataclass
class JobRecord:
    job_id: str
    session_id: str
    job_type: JobType
    state: JobState = "queued"
    stage: str = "queued"
    message: str = "Waiting for the workflow worker"
    completed_steps: int = 0
    total_steps: int = 1
    created_at: str = field(default_factory=utc_now)
    started_at: str | None = None
    finished_at: str | None = None
    error_code: str | None = None
    retryable: bool = False
    cancel_event: threading.Event = field(default_factory=threading.Event, repr=False)


class SessionNotFound(KeyError):
    pass


class SessionExpired(KeyError):
    pass


class ActiveJobExists(RuntimeError):
    pass


class QueueFull(RuntimeError):
    pass


class IdempotencyConflict(RuntimeError):
    pass


class RuntimeState:
    """Own ephemeral data and execute a bounded number of workflows."""

    def __init__(
        self,
        *,
        session_idle_minutes: int,
        max_sessions: int,
        worker_concurrency: int,
        queue_size: int,
    ) -> None:
        self.session_idle_seconds = max(60, session_idle_minutes * 60)
        self.max_sessions = max(1, max_sessions)
        self._lock = threading.RLock()
        self._sessions: dict[str, SessionRecord] = {}
        self._jobs: dict[str, JobRecord] = {}
        self._idempotency: dict[tuple[str, str, str], tuple[str, str]] = {}
        self._executor = ThreadPoolExecutor(
            max_workers=max(1, worker_concurrency),
            thread_name_prefix="interview-workflow",
        )
        self._slots = threading.BoundedSemaphore(max(1, worker_concurrency + queue_size))
        self._started_jobs = 0
        self._failed_jobs = 0
        self._completed_jobs = 0
        self._cancelled_jobs = 0
        self._total_job_seconds = 0.0

    def _cleanup_locked(self) -> None:
        now = time.monotonic()
        expired = [
            session_id
            for session_id, session in self._sessions.items()
            if session.active_job_id is None
            and now - session.last_access_monotonic > self.session_idle_seconds
        ]
        for session_id in expired:
            self._delete_locked(session_id)

    def _delete_locked(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
        job_ids = [
            job_id
            for job_id, job in self._jobs.items()
            if job.session_id == session_id
        ]
        for job_id in job_ids:
            self._jobs.pop(job_id, None)
        keys = [key for key in self._idempotency if key[0] == session_id]
        for key in keys:
            self._idempotency.pop(key, None)

    def create_session(
        self,
        *,
        profile: str,
        job_description: str,
        candidate_profile: str,
        job_description_filename: str,
        candidate_filename: str | None,
        company_hint: str,
        interview_focus: str,
        web_research: bool,
    ) -> SessionRecord:
        with self._lock:
            self._cleanup_locked()
            if len(self._sessions) >= self.max_sessions:
                raise QueueFull("The temporary session capacity is full. Try again shortly.")
            session = SessionRecord(
                session_id=secrets.token_urlsafe(24),
                profile=profile,
                job_description=job_description,
                candidate_profile=candidate_profile,
                job_description_filename=job_description_filename,
                candidate_filename=candidate_filename,
                company_hint=company_hint,
                interview_focus=interview_focus,
                web_research=web_research,
            )
            self._sessions[session.session_id] = session
            return session

    def get_session(self, session_id: str, *, touch: bool = True) -> SessionRecord:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionNotFound(session_id)
            if (
                session.active_job_id is None
                and time.monotonic() - session.last_access_monotonic
                > self.session_idle_seconds
            ):
                self._delete_locked(session_id)
                raise SessionExpired(session_id)
            if touch:
                session.last_access_monotonic = time.monotonic()
            return session

    def delete_session(self, session_id: str) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session and session.active_job_id:
                job = self._jobs.get(session.active_job_id)
                if job and job.state == "queued":
                    job.cancel_event.set()
                    job.state = "cancelled"
                    job.stage = "cancelled"
                    job.message = "Cancelled before execution"
                    job.finished_at = utc_now()
            self._delete_locked(session_id)

    def cancel_job(self, job_id: str) -> JobRecord:
        with self._lock:
            job = self.get_job(job_id)
            if job.state in {"queued", "running"}:
                job.cancel_event.set()
                if job.state == "queued":
                    job.state = "cancelled"
                    job.stage = "cancelled"
                    job.message = "Cancelled before execution"
                    job.finished_at = utc_now()
                    self._cancelled_jobs += 1
                    session = self._sessions.get(job.session_id)
                    if session and session.active_job_id == job_id:
                        session.active_job_id = None
            return job

    def set_package(self, session_id: str, package: InterviewPackage) -> None:
        with self._lock:
            session = self.get_session(session_id, touch=False)
            session.package = package
            session.report = None

    def set_report(self, session_id: str, report: InterviewReport) -> None:
        with self._lock:
            session = self.get_session(session_id, touch=False)
            session.report = report

    def get_job(self, job_id: str) -> JobRecord:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise SessionNotFound(job_id)
            return job

    def submit_job(
        self,
        *,
        session_id: str,
        job_type: JobType,
        idempotency_key: str,
        digest: str,
        operation: JobOperation,
    ) -> JobRecord:
        key = (session_id, job_type, idempotency_key)
        with self._lock:
            session = self.get_session(session_id)
            existing = self._idempotency.get(key)
            if existing:
                existing_digest, existing_job_id = existing
                if existing_digest != digest:
                    raise IdempotencyConflict(
                        "The idempotency key was reused with a different request."
                    )
                return self._jobs[existing_job_id]
            if session.active_job_id:
                active = self._jobs.get(session.active_job_id)
                if active and active.state in {"queued", "running"}:
                    raise ActiveJobExists("This session already has an active workflow.")
            if not self._slots.acquire(blocking=False):
                raise QueueFull("The workflow queue is full. Try again shortly.")

            job = JobRecord(
                job_id=secrets.token_urlsafe(20),
                session_id=session_id,
                job_type=job_type,
            )
            self._jobs[job.job_id] = job
            self._started_jobs += 1
            self._idempotency[key] = (digest, job.job_id)
            session.active_job_id = job.job_id
            self._executor.submit(self._run_job, job.job_id, operation)
            return job

    def _run_job(self, job_id: str, operation: JobOperation) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or job.state == "cancelled":
                self._slots.release()
                return
            job.state = "running"
            job.started_at = utc_now()
            session = self._sessions.get(job.session_id)
            if session is None:
                job.state = "cancelled"
                job.finished_at = utc_now()
                self._slots.release()
                return

        def progress(stage: str, message: str, completed: int, total: int) -> None:
            with self._lock:
                current = self._jobs.get(job_id)
                if current is None:
                    return
                current.stage = stage
                current.message = message
                current.completed_steps = max(0, completed)
                current.total_steps = max(1, total)

        try:
            operation(session, progress, job.cancel_event)
            if job.cancel_event.is_set():
                with self._lock:
                    current = self._jobs.get(job_id)
                    if current:
                        current.state = "cancelled"
                        current.stage = "cancelled"
                        current.message = "Cancelled"
                        current.finished_at = utc_now()
                        self._cancelled_jobs += 1
                return
        except Exception as exc:
            LOGGER.exception(
                "Workflow job %s (%s) failed",
                job_id,
                job.job_type,
            )
            with self._lock:
                current = self._jobs.get(job_id)
                if current:
                    code, message, retryable = safe_job_error(exc)
                    current.state = "failed"
                    current.stage = "failed"
                    current.message = message
                    current.error_code = code
                    current.retryable = retryable
                    current.finished_at = utc_now()
                    self._failed_jobs += 1
        else:
            with self._lock:
                current = self._jobs.get(job_id)
                if current:
                    current.state = "succeeded"
                    current.stage = "complete"
                    current.message = "Workflow completed"
                    current.completed_steps = current.total_steps
                    current.finished_at = utc_now()
                    self._completed_jobs += 1
        finally:
            with self._lock:
                current = self._jobs.get(job_id)
                session_id = current.session_id if current else None
                session = self._sessions.get(session_id) if session_id else None
                if session and session.active_job_id == job_id:
                    session.active_job_id = None
                    session.last_access_monotonic = time.monotonic()
                if current and current.started_at and current.finished_at:
                    started = datetime.fromisoformat(current.started_at)
                    finished = datetime.fromisoformat(current.finished_at)
                    self._total_job_seconds += (finished - started).total_seconds()
            self._slots.release()

    def metrics(self) -> dict[str, int | float]:
        with self._lock:
            active = sum(
                job.state in {"queued", "running"} for job in self._jobs.values()
            )
            failed = self._failed_jobs
            terminal = self._completed_jobs + failed + self._cancelled_jobs
            return {
                "sessions": len(self._sessions),
                "activeJobs": active,
                "queuedJobs": sum(job.state == "queued" for job in self._jobs.values()),
                "runningJobs": sum(job.state == "running" for job in self._jobs.values()),
                "startedJobs": self._started_jobs,
                "completedJobs": self._completed_jobs,
                "failedJobs": failed,
                "cancelledJobs": self._cancelled_jobs,
                "failureRate": round(failed / terminal, 4) if terminal else 0.0,
                "averageJobSeconds": (
                    round(self._total_job_seconds / terminal, 2) if terminal else 0.0
                ),
            }

    def shutdown(self) -> None:
        with self._lock:
            for job in self._jobs.values():
                if job.state in {"queued", "running"}:
                    job.cancel_event.set()
        self._executor.shutdown(wait=True, cancel_futures=True)


def safe_job_error(exc: Exception) -> tuple[str, str, bool]:
    """Map workflow failures to messages safe for a public API."""
    message = str(exc)
    lowered = message.lower()
    if "not reachable" in lowered or "unavailable" in lowered:
        return "MODEL_UNAVAILABLE", message, True
    if "rate limit" in lowered or "429" in lowered:
        return "MODEL_RATE_LIMITED", "The local model is busy. Try again shortly.", True
    if "timed out" in lowered or "timeout" in lowered:
        return "MODEL_TIMEOUT", "The model took too long to respond. Try again.", True
    if "valid" in lowered and ("json" in lowered or "data" in lowered):
        return "STRUCTURED_OUTPUT_INVALID", message, True
    if isinstance(exc, ValueError):
        return "WORKFLOW_VALIDATION_ERROR", message, False
    return (
        "WORKFLOW_FAILED",
        "The workflow could not be completed. Retry or review the server log.",
        True,
    )
