import pytest

from job_interviewer.config import Settings


def test_crewai_model_adds_ollama_prefix() -> None:
    settings = Settings(ollama_model="gemma4:latest")
    assert settings.crewai_model == "ollama/gemma4:latest"


def test_crewai_model_does_not_duplicate_ollama_prefix() -> None:
    settings = Settings(ollama_model="ollama/gemma4:latest")
    assert settings.crewai_model == "ollama/gemma4:latest"


def test_profiles_resolve_expected_local_models_and_limits() -> None:
    settings = Settings()

    assert settings.for_profile("preview").selected_model == "llama3.2:latest"
    assert settings.for_profile("demo").selected_model == "gemma4:latest"
    assert settings.for_profile("deep").selected_model == "gemma4:26b"
    assert settings.profiles["deep"].max_iterations == 3


def test_build_tag_can_be_overridden_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("APP_BUILD_TAG", "fix-ui-tabs.3")

    assert Settings.from_env().build_tag == "fix-ui-tabs.3"


def test_ollama_reasoning_effort_can_be_configured(monkeypatch) -> None:
    monkeypatch.setenv("OLLAMA_REASONING_EFFORT", "low")

    assert Settings.from_env().ollama_reasoning_effort == "low"


def test_profile_policy_can_be_overridden_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("PROFILE_PREVIEW_LABEL", "Quick local check")
    monkeypatch.setenv("PROFILE_PREVIEW_ROLE_QUESTION_COUNT", "4")
    monkeypatch.setenv("PROFILE_PREVIEW_HR_QUESTION_COUNT", "2")
    monkeypatch.setenv("PROFILE_PREVIEW_ANSWER_SELECTION_DEFAULT", "3")
    monkeypatch.setenv("PROFILE_PREVIEW_ANSWER_SELECTION_MAXIMUM", "5")
    monkeypatch.setenv("PROFILE_PREVIEW_MAX_ITERATIONS", "2")
    monkeypatch.setenv("PROFILE_PREVIEW_PASS_SCORE", "3")
    monkeypatch.setenv("PROFILE_PREVIEW_ANSWER_WORD_LIMIT", "100")
    monkeypatch.setenv("PROFILE_PREVIEW_MAX_TOKENS", "3072")
    monkeypatch.setenv("PROFILE_PREVIEW_SEARCH_REGION", "us-en")

    profile = Settings.from_env().profiles["preview"]

    assert profile.label == "Quick local check"
    assert profile.role_question_count == 4
    assert profile.hr_question_count == 2
    assert profile.answer_selection_default == 3
    assert profile.answer_selection_maximum == 5
    assert profile.max_iterations == 2
    assert profile.pass_score == 3
    assert profile.answer_word_limit == 100
    assert profile.max_tokens == 3072
    assert profile.search_region == "us-en"


def test_invalid_profile_environment_value_fails_fast(monkeypatch) -> None:
    monkeypatch.setenv("PROFILE_DEMO_MAX_ITERATIONS", "4")

    with pytest.raises(ValueError):
        Settings.from_env()
