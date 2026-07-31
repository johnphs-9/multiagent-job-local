"""FastAPI application serving the API and compiled React frontend."""

from __future__ import annotations

import secrets
import threading
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

from fastapi import (
    FastAPI,
    File,
    Form,
    Header,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from job_interviewer import __version__
from job_interviewer.api.runtime import (
    ActiveJobExists,
    IdempotencyConflict,
    JobRecord,
    QueueFull,
    RuntimeState,
    SessionExpired,
    SessionNotFound,
    SessionRecord,
    payload_digest,
)
from job_interviewer.config import Settings
from job_interviewer.documents import (
    MAX_FILE_BYTES,
    SUPPORTED_SUFFIXES,
    DocumentError,
    extract_document,
)
from job_interviewer.render import render_report
from job_interviewer.service import (
    build_interview_plan,
    check_ollama,
    improve_interview_answers,
)

API_PREFIX = "/api/v1"
DEFAULT_FOCUS = "balanced company, role, technical, and behavioural coverage"


class ExampleSessionRequest(BaseModel):
    profile: str = "demo"
    company_hint: str = ""
    interview_focus: str = DEFAULT_FOCUS
    web_research: bool = False


class AnswerJobRequest(BaseModel):
    selected_question_ids: list[str] = Field(min_length=1)


def _camel_key(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.capitalize() for part in tail)


def to_camel(value: Any) -> Any:
    """Convert nested model output to the frontend's camelCase API convention."""
    if isinstance(value, dict):
        return {_camel_key(str(key)): to_camel(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_camel(item) for item in value]
    return value


def session_response(session: SessionRecord, settings: Settings) -> dict[str, Any]:
    expires_in = max(
        0,
        int(
            settings.session_idle_minutes * 60
            - (time.monotonic() - session.last_access_monotonic)
        ),
    )
    state = (
        "report_ready"
        if session.report
        else "plan_ready"
        if session.package
        else "evidence_ready"
    )
    return {
        "sessionId": session.session_id,
        "profile": session.profile,
        "state": state,
        "createdAt": session.created_at,
        "expiresInSeconds": expires_in,
        "activeJobId": session.active_job_id,
        "hasPlan": session.package is not None,
        "hasReport": session.report is not None,
        "jobDescriptionFilename": session.job_description_filename,
        "candidateFilename": session.candidate_filename,
    }


def job_response(job: JobRecord) -> dict[str, Any]:
    result_path = (
        f"{API_PREFIX}/sessions/{job.session_id}/plan"
        if job.job_type == "plan"
        else f"{API_PREFIX}/sessions/{job.session_id}/report"
    )
    return {
        "jobId": job.job_id,
        "sessionId": job.session_id,
        "type": job.job_type,
        "state": job.state,
        "stage": job.stage,
        "message": job.message,
        "completedSteps": job.completed_steps,
        "totalSteps": job.total_steps,
        "createdAt": job.created_at,
        "startedAt": job.started_at,
        "finishedAt": job.finished_at,
        "errorCode": job.error_code,
        "retryable": job.retryable,
        "resultUrl": result_path if job.state == "succeeded" else None,
    }


def error_response(
    status_code: int,
    code: str,
    message: str,
    *,
    retryable: bool = False,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "retryable": retryable,
            }
        },
    )


class RateLimiter:
    """Small single-process limiter appropriate for the demo deployment."""

    def __init__(self, limit: int, window_seconds: int = 3600) -> None:
        self.limit = max(1, limit)
        self.window = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            events = self._events[key]
            while events and now - events[0] > self.window:
                events.popleft()
            if len(events) >= self.limit:
                return False
            events.append(now)
            return True


async def _read_upload(upload: UploadFile, *, required: bool) -> str:
    content = await upload.read(MAX_FILE_BYTES + 1)
    if len(content) > MAX_FILE_BYTES:
        raise DocumentError(
            f"Files must be no larger than {MAX_FILE_BYTES // 1024 // 1024} MB."
        )
    if not content and not required:
        return ""
    return extract_document(upload.filename or "upload.txt", content)


def _display_filename(filename: str | None, fallback: str) -> str:
    """Return a path-free filename suitable for ephemeral UI metadata."""
    cleaned = (filename or "").replace("\\", "/").rsplit("/", 1)[-1].strip()
    return cleaned or fallback


def _resolve_frontend_dir(settings: Settings) -> Path:
    if settings.frontend_dist_dir:
        return Path(settings.frontend_dist_dir).expanduser().resolve()
    return Path(__file__).resolve().parents[3] / "frontend" / "dist"


def create_app(settings: Settings | None = None) -> FastAPI:
    base_settings = settings or Settings.from_env()
    runtime = RuntimeState(
        session_idle_minutes=base_settings.session_idle_minutes,
        max_sessions=base_settings.max_sessions,
        worker_concurrency=base_settings.job_worker_concurrency,
        queue_size=base_settings.job_queue_size,
    )
    limiter = RateLimiter(base_settings.request_limit_per_hour)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        yield
        runtime.shutdown()

    app = FastAPI(
        title="Agentic Interview Coach API",
        version=__version__,
        lifespan=lifespan,
    )
    app.state.runtime = runtime
    app.state.settings = base_settings

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        return response

    def client_key(request: Request) -> str:
        return request.client.host if request.client else "unknown"

    def enforce_rate(request: Request) -> None:
        if not limiter.allow(client_key(request)):
            raise HTTPException(
                status_code=429,
                detail="Request limit reached. Try again later.",
            )

    def resolve_profile(profile_name: str) -> Settings:
        try:
            return base_settings.for_profile(profile_name)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    def get_session_or_error(session_id: str) -> SessionRecord:
        try:
            return runtime.get_session(session_id)
        except SessionExpired as exc:
            raise HTTPException(status_code=410, detail="Session expired.") from exc
        except SessionNotFound as exc:
            raise HTTPException(status_code=404, detail="Session not found.") from exc

    @app.exception_handler(DocumentError)
    async def document_error_handler(_request: Request, exc: DocumentError):
        return error_response(422, "INVALID_DOCUMENT", str(exc))

    @app.exception_handler(QueueFull)
    async def queue_error_handler(_request: Request, exc: QueueFull):
        return error_response(503, "QUEUE_FULL", str(exc), retryable=True)

    @app.exception_handler(ActiveJobExists)
    async def active_job_handler(_request: Request, exc: ActiveJobExists):
        return error_response(409, "ACTIVE_JOB_EXISTS", str(exc))

    @app.exception_handler(IdempotencyConflict)
    async def idempotency_handler(_request: Request, exc: IdempotencyConflict):
        return error_response(409, "IDEMPOTENCY_CONFLICT", str(exc))

    @app.get(f"{API_PREFIX}/health/live")
    async def live() -> dict[str, str]:
        return {
            "status": "ok",
            "version": __version__,
            "buildTag": base_settings.build_tag,
        }

    @app.get(f"{API_PREFIX}/health/ready")
    async def ready() -> dict[str, str]:
        status = check_ollama(
            base_settings.ollama_base_url,
            base_settings.selected_model,
        )
        if not status.ok:
            raise HTTPException(status_code=503, detail=status.message)
        return {
            "status": "ready",
            "version": __version__,
            "buildTag": base_settings.build_tag,
        }

    @app.get(f"{API_PREFIX}/config")
    async def public_config() -> dict[str, Any]:
        profiles = []
        for profile in base_settings.profiles.values():
            if profile.name == "deep" and not base_settings.enable_deep_profile:
                continue
            profile_settings = base_settings.for_profile(profile.name)
            profiles.append(
                {
                    "id": profile.name,
                    "label": profile.label,
                    "description": profile.description,
                    "model": profile_settings.selected_model,
                    "roleQuestionCount": profile.role_question_count,
                    "hrQuestionCount": profile.hr_question_count,
                    "defaultAnswerCount": profile.answer_selection_default,
                    "maxAnswerCount": profile.answer_selection_maximum,
                    "maxIterations": profile.max_iterations,
                    "passScore": profile.pass_score,
                }
            )
        return {
            "appVersion": __version__,
            "buildTag": base_settings.build_tag,
            "profiles": profiles,
            "defaultProfile": base_settings.model_profile,
            "maxUploadBytes": MAX_FILE_BYTES,
            "supportedExtensions": sorted(SUPPORTED_SUFFIXES),
            "sessionIdleMinutes": base_settings.session_idle_minutes,
        }

    @app.post(f"{API_PREFIX}/sessions", status_code=201)
    async def create_session(
        request: Request,
        job_description: Annotated[UploadFile, File()],
        candidate_profile: Annotated[UploadFile | None, File()] = None,
        candidate_notes: Annotated[str, Form()] = "",
        company_hint: Annotated[str, Form()] = "",
        interview_focus: Annotated[str, Form()] = DEFAULT_FOCUS,
        web_research: Annotated[bool, Form()] = True,
        profile: Annotated[str, Form()] = "demo",
    ) -> dict[str, Any]:
        enforce_rate(request)
        resolved = resolve_profile(profile)
        jd_text = await _read_upload(job_description, required=True)
        candidate_parts: list[str] = []
        if candidate_profile is not None:
            candidate_parts.append(await _read_upload(candidate_profile, required=False))
        if candidate_notes.strip():
            candidate_parts.append(candidate_notes.strip())
        candidate_text = "\n\n".join(part for part in candidate_parts if part.strip())
        if not candidate_text:
            raise HTTPException(
                status_code=422,
                detail="Upload a candidate profile or provide candidate notes.",
            )
        session = runtime.create_session(
            profile=resolved.model_profile,
            job_description=jd_text,
            candidate_profile=candidate_text,
            job_description_filename=_display_filename(
                job_description.filename, "job-description.txt"
            ),
            candidate_filename=(
                _display_filename(candidate_profile.filename, "candidate-profile.txt")
                if candidate_profile is not None
                else None
            ),
            company_hint=company_hint.strip(),
            interview_focus=interview_focus.strip() or DEFAULT_FOCUS,
            web_research=web_research,
        )
        return session_response(session, base_settings)

    @app.post(f"{API_PREFIX}/sessions/examples", status_code=201)
    async def create_example_session(
        body: ExampleSessionRequest,
        request: Request,
    ) -> dict[str, Any]:
        enforce_rate(request)
        resolved = resolve_profile(body.profile)
        root = Path(__file__).resolve().parents[3]
        jd_text = (root / "examples" / "job_description.txt").read_text(encoding="utf-8")
        candidate_text = (root / "examples" / "candidate_profile.txt").read_text(
            encoding="utf-8"
        )
        session = runtime.create_session(
            profile=resolved.model_profile,
            job_description=jd_text,
            candidate_profile=candidate_text,
            job_description_filename="job_description.txt",
            candidate_filename="candidate_profile.txt",
            company_hint=body.company_hint.strip(),
            interview_focus=body.interview_focus.strip() or DEFAULT_FOCUS,
            web_research=body.web_research,
        )
        return session_response(session, base_settings)

    @app.get(f"{API_PREFIX}/sessions/{{session_id}}")
    async def get_session(session_id: str) -> dict[str, Any]:
        return session_response(get_session_or_error(session_id), base_settings)

    @app.delete(f"{API_PREFIX}/sessions/{{session_id}}", status_code=204)
    async def delete_session(session_id: str) -> Response:
        runtime.delete_session(session_id)
        return Response(status_code=204)

    @app.post(f"{API_PREFIX}/sessions/{{session_id}}/plan-jobs", status_code=202)
    async def create_plan_job(
        session_id: str,
        request: Request,
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> dict[str, Any]:
        enforce_rate(request)
        session = get_session_or_error(session_id)
        selected_settings = resolve_profile(session.profile)

        def run_plan(
            current: SessionRecord,
            progress,
        ) -> None:
            status = check_ollama(
                selected_settings.ollama_base_url,
                selected_settings.selected_model,
            )
            if not status.ok:
                raise RuntimeError(status.message)
            options = selected_settings.profile.options(
                interview_focus=current.interview_focus,
                web_research=current.web_research,
            )
            package = build_interview_plan(
                job_description=current.job_description,
                candidate_profile=current.candidate_profile,
                settings=selected_settings,
                options=options,
                company_hint=current.company_hint,
                progress=progress,
            )
            runtime.set_package(current.session_id, package)

        key = idempotency_key or secrets.token_urlsafe(18)
        job = runtime.submit_job(
            session_id=session_id,
            job_type="plan",
            idempotency_key=key,
            digest=payload_digest({"profile": session.profile}),
            operation=run_plan,
        )
        return job_response(job)

    @app.get(f"{API_PREFIX}/sessions/{{session_id}}/plan")
    async def get_plan(session_id: str) -> dict[str, Any]:
        session = get_session_or_error(session_id)
        if session.package is None:
            raise HTTPException(status_code=409, detail="Interview plan is not ready.")
        return to_camel(jsonable_encoder(session.package))

    @app.post(f"{API_PREFIX}/sessions/{{session_id}}/answer-jobs", status_code=202)
    async def create_answer_job(
        session_id: str,
        body: AnswerJobRequest,
        request: Request,
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> dict[str, Any]:
        enforce_rate(request)
        session = get_session_or_error(session_id)
        if session.package is None:
            raise HTTPException(status_code=409, detail="Build an interview plan first.")
        selected_settings = resolve_profile(session.profile)
        unique_ids = list(dict.fromkeys(body.selected_question_ids))
        if len(unique_ids) != len(body.selected_question_ids):
            raise HTTPException(status_code=422, detail="Question IDs must be unique.")
        known_ids = {
            question.question_id for question in session.package.interview_plan.all_questions
        }
        unknown = set(unique_ids) - known_ids
        if unknown:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown question IDs: {sorted(unknown)}",
            )
        if len(unique_ids) > selected_settings.profile.answer_selection_maximum:
            raise HTTPException(
                status_code=422,
                detail=(
                    "This profile allows at most "
                    f"{selected_settings.profile.answer_selection_maximum} answers."
                ),
            )

        def run_answers(current: SessionRecord, progress) -> None:
            if current.package is None:
                raise ValueError("Interview plan is not available.")
            status = check_ollama(
                selected_settings.ollama_base_url,
                selected_settings.selected_model,
            )
            if not status.ok:
                raise RuntimeError(status.message)
            report = improve_interview_answers(
                package=current.package,
                candidate_profile=current.candidate_profile,
                settings=selected_settings,
                selected_question_ids=unique_ids,
                progress=progress,
            )
            runtime.set_report(current.session_id, report)

        key = idempotency_key or secrets.token_urlsafe(18)
        job = runtime.submit_job(
            session_id=session_id,
            job_type="answers",
            idempotency_key=key,
            digest=payload_digest({"question_ids": unique_ids}),
            operation=run_answers,
        )
        return job_response(job)

    @app.get(f"{API_PREFIX}/sessions/{{session_id}}/report")
    async def get_report(session_id: str) -> dict[str, Any]:
        session = get_session_or_error(session_id)
        if session.report is None:
            raise HTTPException(status_code=409, detail="Interview report is not ready.")
        return to_camel(jsonable_encoder(session.report))

    @app.get(f"{API_PREFIX}/jobs/{{job_id}}")
    async def get_job(job_id: str) -> dict[str, Any]:
        try:
            return job_response(runtime.get_job(job_id))
        except SessionNotFound as exc:
            raise HTTPException(status_code=404, detail="Job not found.") from exc

    @app.get(f"{API_PREFIX}/sessions/{{session_id}}/downloads/report.md")
    async def download_markdown(session_id: str) -> Response:
        session = get_session_or_error(session_id)
        if session.report is None:
            raise HTTPException(status_code=409, detail="Interview report is not ready.")
        return Response(
            content=render_report(session.report),
            media_type="text/markdown",
            headers={
                "Content-Disposition": 'attachment; filename="interview-report.md"'
            },
        )

    @app.get(f"{API_PREFIX}/sessions/{{session_id}}/downloads/report.json")
    async def download_json(session_id: str) -> Response:
        session = get_session_or_error(session_id)
        if session.report is None:
            raise HTTPException(status_code=409, detail="Interview report is not ready.")
        return Response(
            content=session.report.model_dump_json(indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": 'attachment; filename="interview-report.json"'
            },
        )

    frontend_dir = _resolve_frontend_dir(base_settings)
    assets_dir = frontend_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def frontend(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found.")
        requested = frontend_dir / full_path
        if full_path and requested.is_file() and frontend_dir in requested.resolve().parents:
            return FileResponse(requested)
        index = frontend_dir / "index.html"
        if index.is_file():
            return FileResponse(index)
        return JSONResponse(
            status_code=503,
            content={
                "message": (
                    "Frontend build not found. Run `cd frontend && npm install && "
                    "npm run build`, or use the Vite development server."
                )
            },
        )

    return app


app = create_app()
