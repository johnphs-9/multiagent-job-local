"""Local Ollama and workflow-profile configuration."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import Literal

from dotenv import load_dotenv

from interview_local import __build_tag__
from interview_local.schemas import WorkflowOptions

ProfileName = Literal["preview", "demo", "deep"]


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_optional_int(name: str) -> int | None:
    value = os.getenv(name)
    if not value or not value.strip():
        return None
    return _parse_env_int(name, value)


def _parse_env_int(name: str, value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer.") from exc


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return default if value is None else _parse_env_int(name, value)


@dataclass(frozen=True)
class WorkflowProfile:
    """Server-authoritative workflow and output limits for a user-visible profile."""

    name: ProfileName
    label: str
    description: str
    role_question_count: int
    hr_question_count: int
    answer_selection_default: int
    answer_selection_maximum: int
    max_iterations: int
    pass_score: int
    answer_word_limit: int
    max_tokens: int
    search_region: str

    def __post_init__(self) -> None:
        WorkflowOptions(
            role_question_count=self.role_question_count,
            hr_question_count=self.hr_question_count,
            max_iterations=self.max_iterations,
            pass_score=self.pass_score,
            answer_word_limit=self.answer_word_limit,
            search_region=self.search_region,
        )
        question_total = self.role_question_count + self.hr_question_count
        if not 1 <= self.answer_selection_default <= question_total:
            raise ValueError(
                f"{self.name} answer_selection_default must be between 1 and "
                f"{question_total}."
            )
        if not (
            self.answer_selection_default
            <= self.answer_selection_maximum
            <= question_total
        ):
            raise ValueError(
                f"{self.name} answer_selection_maximum must be between "
                "answer_selection_default and the total question count."
            )
        if self.max_tokens < 1:
            raise ValueError(f"{self.name} max_tokens must be positive.")
        if (
            not self.label.strip()
            or not self.description.strip()
            or not self.search_region.strip()
        ):
            raise ValueError(
                f"{self.name} label, description, and search_region are required."
            )

    def options(
        self,
        *,
        interview_focus: str,
        web_research: bool,
    ) -> WorkflowOptions:
        return WorkflowOptions(
            role_question_count=self.role_question_count,
            hr_question_count=self.hr_question_count,
            max_iterations=self.max_iterations,
            pass_score=self.pass_score,
            answer_word_limit=self.answer_word_limit,
            interview_focus=interview_focus,
            web_research=web_research,
            search_region=self.search_region,
        )


DEFAULT_PROFILES: dict[ProfileName, WorkflowProfile] = {
    "preview": WorkflowProfile(
        name="preview",
        label="Ultra-fast preview",
        description="A minimal walkthrough with three role questions and one HR question.",
        role_question_count=3,
        hr_question_count=1,
        answer_selection_default=2,
        answer_selection_maximum=3,
        max_iterations=1,
        pass_score=4,
        answer_word_limit=80,
        max_tokens=2048,
        search_region="sg-en",
    ),
    "demo": WorkflowProfile(
        name="demo",
        label="Fast demo",
        description="The recommended demonstration with concise answers and one review pass.",
        role_question_count=6,
        hr_question_count=2,
        answer_selection_default=4,
        answer_selection_maximum=6,
        max_iterations=1,
        pass_score=4,
        answer_word_limit=120,
        max_tokens=4096,
        search_region="sg-en",
    ),
    "deep": WorkflowProfile(
        name="deep",
        label="Deep analysis",
        description="A comprehensive private run with more questions and up to three reviews.",
        role_question_count=20,
        hr_question_count=6,
        answer_selection_default=26,
        answer_selection_maximum=26,
        max_iterations=3,
        pass_score=4,
        answer_word_limit=180,
        max_tokens=8192,
        search_region="sg-en",
    ),
}


def profiles_from_env() -> dict[ProfileName, WorkflowProfile]:
    """Build all workflow profiles from environment values and validated defaults."""
    profiles: dict[ProfileName, WorkflowProfile] = {}
    for name, default in DEFAULT_PROFILES.items():
        prefix = f"PROFILE_{name.upper()}_"
        profiles[name] = WorkflowProfile(
            name=name,
            label=os.getenv(f"{prefix}LABEL", default.label),
            description=os.getenv(f"{prefix}DESCRIPTION", default.description),
            role_question_count=_env_int(
                f"{prefix}ROLE_QUESTION_COUNT", default.role_question_count
            ),
            hr_question_count=_env_int(
                f"{prefix}HR_QUESTION_COUNT", default.hr_question_count
            ),
            answer_selection_default=_env_int(
                f"{prefix}ANSWER_SELECTION_DEFAULT",
                default.answer_selection_default,
            ),
            answer_selection_maximum=_env_int(
                f"{prefix}ANSWER_SELECTION_MAXIMUM",
                default.answer_selection_maximum,
            ),
            max_iterations=_env_int(
                f"{prefix}MAX_ITERATIONS", default.max_iterations
            ),
            pass_score=_env_int(f"{prefix}PASS_SCORE", default.pass_score),
            answer_word_limit=_env_int(
                f"{prefix}ANSWER_WORD_LIMIT", default.answer_word_limit
            ),
            max_tokens=_env_int(f"{prefix}MAX_TOKENS", default.max_tokens),
            search_region=os.getenv(
                f"{prefix}SEARCH_REGION", default.search_region
            ),
        )
    return profiles


def get_profile(
    name: str,
    profiles: Mapping[ProfileName, WorkflowProfile] | None = None,
) -> WorkflowProfile:
    """Return a validated profile by name."""
    available = profiles if profiles is not None else DEFAULT_PROFILES
    normalized = name.strip().lower()
    if normalized not in available:
        choices = ", ".join(available)
        raise ValueError(f"Unknown model profile `{name}`. Choose one of: {choices}.")
    return available[normalized]  # type: ignore[index]


@dataclass(frozen=True)
class Settings:
    """Local Ollama and web application configuration."""

    model_profile: ProfileName = "demo"
    profiles: dict[ProfileName, WorkflowProfile] = field(
        default_factory=lambda: dict(DEFAULT_PROFILES)
    )

    ollama_base_url: str = "http://localhost:11434"
    ollama_preview_model: str = "llama3.2:latest"
    ollama_demo_model: str = "gemma4:latest"
    ollama_deep_model: str = "gemma4:26b"
    ollama_reasoning_effort: Literal["none", "low", "medium", "high"] = "none"
    ollama_model: str | None = None

    llm_timeout_seconds: float = 600.0
    llm_max_tokens: int | None = None
    enable_deep_profile: bool = True
    session_idle_minutes: int = 60
    max_sessions: int = 50
    job_worker_concurrency: int = 1
    job_queue_size: int = 5
    request_limit_per_hour: int = 20
    frontend_dist_dir: str = ""
    build_tag: str = __build_tag__

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv()
        profile = os.getenv("DEFAULT_MODEL_PROFILE", cls.model_profile).strip().lower()
        reasoning_effort = os.getenv(
            "OLLAMA_REASONING_EFFORT", cls.ollama_reasoning_effort
        ).strip().lower()
        if reasoning_effort not in {"none", "low", "medium", "high"}:
            raise ValueError(
                "OLLAMA_REASONING_EFFORT must be `none`, `low`, `medium`, or `high`."
            )
        profiles = profiles_from_env()
        get_profile(profile, profiles)
        return cls(
            model_profile=profile,  # type: ignore[arg-type]
            profiles=profiles,
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", cls.ollama_base_url),
            ollama_preview_model=os.getenv(
                "OLLAMA_PREVIEW_MODEL", cls.ollama_preview_model
            ),
            ollama_demo_model=os.getenv("OLLAMA_DEMO_MODEL", cls.ollama_demo_model),
            ollama_deep_model=os.getenv("OLLAMA_DEEP_MODEL", cls.ollama_deep_model),
            ollama_reasoning_effort=reasoning_effort,  # type: ignore[arg-type]
            ollama_model=os.getenv("OLLAMA_MODEL") or None,
            llm_timeout_seconds=float(
                os.getenv("LLM_TIMEOUT_SECONDS", cls.llm_timeout_seconds)
            ),
            llm_max_tokens=_env_optional_int("LLM_MAX_TOKENS"),
            enable_deep_profile=_env_bool("ENABLE_DEEP_PROFILE", cls.enable_deep_profile),
            session_idle_minutes=int(
                os.getenv("SESSION_IDLE_MINUTES", cls.session_idle_minutes)
            ),
            max_sessions=int(os.getenv("MAX_SESSIONS", cls.max_sessions)),
            job_worker_concurrency=int(
                os.getenv("JOB_WORKER_CONCURRENCY", cls.job_worker_concurrency)
            ),
            job_queue_size=int(os.getenv("JOB_QUEUE_SIZE", cls.job_queue_size)),
            request_limit_per_hour=int(
                os.getenv("REQUEST_LIMIT_PER_HOUR", cls.request_limit_per_hour)
            ),
            frontend_dist_dir=os.getenv("FRONTEND_DIST_DIR", ""),
            build_tag=os.getenv("APP_BUILD_TAG", cls.build_tag).strip()
            or cls.build_tag,
        )

    @property
    def profile(self) -> WorkflowProfile:
        return get_profile(self.model_profile, self.profiles)

    @property
    def selected_model(self) -> str:
        if self.ollama_model:
            return self.ollama_model.removeprefix("ollama/")
        return {
            "preview": self.ollama_preview_model,
            "demo": self.ollama_demo_model,
            "deep": self.ollama_deep_model,
        }[self.model_profile]

    @property
    def selected_max_tokens(self) -> int:
        return self.llm_max_tokens or self.profile.max_tokens

    @property
    def crewai_model(self) -> str:
        """Return CrewAI/LiteLLM's Ollama-qualified model name."""
        model = self.selected_model
        return model if model.startswith("ollama/") else f"ollama/{model}"

    def for_profile(self, profile: str) -> Settings:
        resolved = get_profile(profile, self.profiles)
        if resolved.name == "deep" and not self.enable_deep_profile:
            raise ValueError("Deep analysis is disabled in this deployment.")
        return replace(
            self,
            model_profile=resolved.name,
            # A global model override applies only before a profile is selected.
            ollama_model=None,
        )
