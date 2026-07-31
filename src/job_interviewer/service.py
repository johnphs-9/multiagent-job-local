"""Application services shared by the HTML application and command-line interface."""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from job_interviewer.config import Settings
from job_interviewer.progress import ProgressCallback
from job_interviewer.schemas import (
    AnswerFlowState,
    InterviewPackage,
    InterviewReport,
    WorkflowOptions,
)


@dataclass(frozen=True)
class OllamaStatus:
    ok: bool
    message: str


def _plain_model_name(model: str) -> str:
    return model.removeprefix("ollama/")


def check_ollama(base_url: str, model: str, timeout: float = 3.0) -> OllamaStatus:
    """Check that Ollama is reachable and the configured model is installed."""
    url = f"{base_url.rstrip('/')}/api/tags"
    try:
        with urlopen(url, timeout=timeout) as response:  # noqa: S310 - configurable endpoint
            payload = json.load(response)
    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        return OllamaStatus(
            False,
            f"Ollama is not reachable at {base_url}. Start it with `ollama serve`. ({exc})",
        )

    installed = {
        str(item.get("name"))
        for item in payload.get("models", [])
        if isinstance(item, dict) and item.get("name")
    }
    requested = _plain_model_name(model)
    aliases = {requested, f"{requested}:latest"} if ":" not in requested else {requested}
    if installed.isdisjoint(aliases):
        names = ", ".join(sorted(installed)) or "none"
        return OllamaStatus(
            False,
            f"Model `{requested}` is not installed. Available models: {names}.",
        )
    return OllamaStatus(True, f"Ollama is ready with `{requested}`.")


def _validate_inputs(job_description: str, candidate_profile: str) -> None:
    if not job_description.strip():
        raise ValueError("Job description cannot be empty.")
    if not candidate_profile.strip():
        raise ValueError(
            "A candidate CV/profile is required so answer agents do not invent experience."
        )


def build_interview_plan(
    *,
    job_description: str,
    candidate_profile: str,
    settings: Settings,
    options: WorkflowOptions,
    company_hint: str = "",
    verbose: bool = False,
    progress: ProgressCallback | None = None,
) -> InterviewPackage:
    """Run identity, company research, JD analysis, and question-design agents."""
    from job_interviewer.crew import PreparationCrew

    _validate_inputs(job_description, candidate_profile)
    return PreparationCrew(settings, verbose=verbose, progress=progress).run(
        job_description=job_description.strip(),
        candidate_profile=candidate_profile.strip(),
        options=options,
        company_hint=company_hint.strip(),
    )


def improve_interview_answers(
    *,
    package: InterviewPackage,
    candidate_profile: str,
    settings: Settings,
    selected_question_ids: list[str] | None = None,
    verbose: bool = False,
    progress: ProgressCallback | None = None,
) -> InterviewReport:
    """Run the bounded answer/evaluate/revise Flow."""
    from job_interviewer.answer_flow import AnswerImprovementFlow

    if not candidate_profile.strip():
        raise ValueError("Candidate profile cannot be empty.")
    ordered_ids = [
        question.question_id for question in package.interview_plan.all_questions
    ]
    valid_ids = set(ordered_ids)
    selected = list(dict.fromkeys(selected_question_ids or ordered_ids))
    unknown = set(selected) - valid_ids
    if unknown:
        raise ValueError(f"Unknown question IDs selected: {sorted(unknown)}")

    state = AnswerFlowState(
        package=package,
        candidate_profile=candidate_profile.strip(),
        selected_question_ids=selected,
    )
    flow = AnswerImprovementFlow(settings, verbose=verbose, progress=progress)
    result = flow.kickoff(inputs=state.model_dump(mode="json"))
    if isinstance(result, InterviewReport):
        return result
    return InterviewReport.model_validate(result)


def run_full_workflow(
    *,
    job_description: str,
    candidate_profile: str,
    settings: Settings,
    options: WorkflowOptions,
    company_hint: str = "",
    verbose: bool = False,
) -> InterviewReport:
    """Run preparation and answer improvement end to end."""
    package = build_interview_plan(
        job_description=job_description,
        candidate_profile=candidate_profile,
        settings=settings,
        options=options,
        company_hint=company_hint,
        verbose=verbose,
    )
    return improve_interview_answers(
        package=package,
        candidate_profile=candidate_profile,
        settings=settings,
        verbose=verbose,
    )
