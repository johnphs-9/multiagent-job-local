import importlib
import time
from types import SimpleNamespace

from fastapi.testclient import TestClient

from interview_local.config import Settings
from interview_local.schemas import (
    AnswerDraft,
    AnswerEvaluation,
    CompanyResearch,
    InterviewPackage,
    InterviewPlan,
    InterviewQuestion,
    InterviewReport,
    JDAnalysis,
    JobIdentity,
    WorkflowOptions,
)

api_module = importlib.import_module("interview_local.api.app")


def sample_package() -> InterviewPackage:
    return InterviewPackage(
        identity=JobIdentity(
            company_name="Example Labs",
            role_title="ML Engineer",
            confidence="high",
            evidence="Named in the job description.",
        ),
        company_research=CompanyResearch(
            company_name="Example Labs",
            summary="A safe example company.",
        ),
        jd_analysis=JDAnalysis(
            role_title="ML Engineer",
            role_summary="Build reliable ML services.",
        ),
        interview_plan=InterviewPlan(
            company_name="Example Labs",
            role_title="ML Engineer",
            role_company_questions=[
                InterviewQuestion(
                    question_id="RC01",
                    group="role_company",
                    category="Technical",
                    question="How would you make an ML service reliable?",
                    rationale="Tests role-specific engineering judgment.",
                )
            ],
            hr_questions=[
                InterviewQuestion(
                    question_id="HR01",
                    group="hr",
                    category="Behavioural",
                    question="Tell me about a difficult collaboration.",
                    rationale="Tests reflection and communication.",
                )
            ],
        ),
        options=WorkflowOptions(
            role_question_count=3,
            hr_question_count=1,
            max_iterations=1,
            answer_word_limit=80,
            web_research=False,
        ),
    )


def wait_for_terminal(client: TestClient, job_id: str) -> dict:
    for _ in range(100):
        response = client.get(f"/api/v1/jobs/{job_id}")
        assert response.status_code == 200
        job = response.json()
        if job["state"] not in {"queued", "running"}:
            return job
        time.sleep(0.01)
    raise AssertionError("background job did not finish")


def test_config_exposes_local_profile_models() -> None:
    settings = Settings(build_tag="test-fix.7")
    with TestClient(api_module.create_app(settings)) as client:
        response = client.get("/api/v1/config")

    assert response.status_code == 200
    payload = response.json()
    assert [profile["id"] for profile in payload["profiles"]] == [
        "preview",
        "demo",
        "deep",
    ]
    assert payload["profiles"][0]["model"] == "llama3.2:latest"
    assert payload["profiles"][0]["passScore"] == 4
    assert payload["appVersion"] == "0.2.3"
    assert payload["buildTag"] == "test-fix.7"


def test_liveness_exposes_version_and_build_tag() -> None:
    settings = Settings(build_tag="ci.42")
    with TestClient(api_module.create_app(settings)) as client:
        response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": "0.2.3",
        "buildTag": "ci.42",
    }


def test_example_plan_and_answer_workflow(monkeypatch) -> None:
    package = sample_package()

    def fake_plan(*, progress, **_kwargs):
        progress("question_design", "Designing questions", 4, 5)
        return package

    def fake_answers(*, selected_question_ids, progress, **_kwargs):
        progress("evaluating_answers", "Evaluating answers", 2, 3)
        question_id = selected_question_ids[0]
        return InterviewReport(
            package=package,
            answers=[
                AnswerDraft(
                    question_id=question_id,
                    answer="I would define service-level objectives and test failure modes.",
                )
            ],
            evaluations=[AnswerEvaluation(question_id=question_id, score=4)],
            iterations_completed=1,
            stopped_early=True,
        )

    monkeypatch.setattr(api_module, "build_interview_plan", fake_plan)
    monkeypatch.setattr(api_module, "improve_interview_answers", fake_answers)
    monkeypatch.setattr(
        api_module,
        "check_ollama",
        lambda *_args, **_kwargs: SimpleNamespace(ok=True, message="ready"),
    )
    settings = Settings(
        model_profile="preview",
        request_limit_per_hour=100,
        session_idle_minutes=5,
    )

    with TestClient(api_module.create_app(settings)) as client:
        created = client.post(
            "/api/v1/sessions/examples",
            json={"profile": "preview", "web_research": False},
        )
        assert created.status_code == 201
        assert created.json()["jobDescriptionFilename"] == "job_description.txt"
        assert created.json()["candidateFilename"] == "candidate_profile.txt"
        session_id = created.json()["sessionId"]

        started = client.post(
            f"/api/v1/sessions/{session_id}/plan-jobs",
            headers={"Idempotency-Key": "plan-test-key"},
        )
        assert started.status_code == 202
        plan_job = wait_for_terminal(client, started.json()["jobId"])
        assert plan_job["state"] == "succeeded"

        plan = client.get(f"/api/v1/sessions/{session_id}/plan")
        assert plan.status_code == 200
        assert plan.json()["identity"]["companyName"] == "Example Labs"

        answer_started = client.post(
            f"/api/v1/sessions/{session_id}/answer-jobs",
            headers={"Idempotency-Key": "answer-test-key"},
            json={"selected_question_ids": ["RC01"]},
        )
        assert answer_started.status_code == 202
        answer_job = wait_for_terminal(client, answer_started.json()["jobId"])
        assert answer_job["state"] == "succeeded"

        report = client.get(f"/api/v1/sessions/{session_id}/report")
        assert report.status_code == 200
        assert report.json()["answers"][0]["questionId"] == "RC01"

        markdown = client.get(
            f"/api/v1/sessions/{session_id}/downloads/report.md"
        )
        assert markdown.status_code == 200
        assert "interview-report.md" in markdown.headers["content-disposition"]


def test_upload_requires_candidate_evidence() -> None:
    settings = Settings(request_limit_per_hour=100)
    with TestClient(api_module.create_app(settings)) as client:
        response = client.post(
            "/api/v1/sessions",
            files={"job_description": ("job.txt", b"Example role", "text/plain")},
            data={"profile": "preview"},
        )

    assert response.status_code == 422
    assert "candidate" in response.json()["detail"].lower()


def test_upload_session_retains_path_free_display_filenames() -> None:
    settings = Settings(request_limit_per_hour=100)
    with TestClient(api_module.create_app(settings)) as client:
        response = client.post(
            "/api/v1/sessions",
            files={
                "job_description": (
                    "roles/platform-lead-description.txt",
                    b"Example role",
                    "text/plain",
                ),
                "candidate_profile": (
                    "private/candidate-profile.txt",
                    b"Example evidence",
                    "text/plain",
                ),
            },
            data={"profile": "preview"},
        )

    assert response.status_code == 201
    assert response.json()["jobDescriptionFilename"] == "platform-lead-description.txt"
    assert response.json()["candidateFilename"] == "candidate-profile.txt"
