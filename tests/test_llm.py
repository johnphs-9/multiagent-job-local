from interview_local.config import Settings
from interview_local.llm import (
    create_llm,
    schema_instruction,
    structured_result,
    structured_result_with_retry,
)
from interview_local.schemas import InterviewPlan


class RawResult:
    def __init__(self, raw: str) -> None:
        self.raw = raw
        self.pydantic = None


class RetryAgent:
    def __init__(self) -> None:
        self.calls = 0

    def kickoff(self, prompt: str) -> RawResult:
        self.calls += 1
        assert "Correct the following invalid InterviewPlan output" in prompt
        return RawResult(
            """
            {
              "company_name": "Example",
              "role_title": "Engineer",
              "role_company_questions": [],
              "hr_questions": []
            }
            """
        )


class EmptyRetryAgent:
    def kickoff(self, _prompt: str) -> RawResult:
        raise ValueError("Invalid response from LLM call - None or empty.")


def test_structured_result_repairs_missing_comma() -> None:
    malformed = """
    {
      "company_name": "Example",
      "role_title": "Engineer",
      "role_company_questions": []
      "hr_questions": []
    }
    """

    result = structured_result(RawResult(malformed), InterviewPlan)

    assert result.company_name == "Example"
    assert result.role_company_questions == []
    assert result.hr_questions == []


def test_schema_instruction_requires_plain_json() -> None:
    instruction = schema_instruction(InterviewPlan)

    assert "Return exactly one JSON object" in instruction
    assert '"company_name"' in instruction
    assert '"$defs"' not in instruction
    assert '"properties"' not in instruction


def test_structured_result_retries_once_for_schema_failure() -> None:
    agent = RetryAgent()

    result = structured_result_with_retry(
        RawResult('{"company_name": "Example"}'),
        InterviewPlan,
        agent,
    )

    assert result.role_title == "Engineer"
    assert agent.calls == 1


def test_create_llm_disables_hidden_ollama_thinking() -> None:
    llm = create_llm(Settings().for_profile("deep"))

    assert llm.additional_params["reasoning_effort"] == "none"
    params = llm._prepare_completion_params(  # noqa: SLF001
        [{"role": "user", "content": "Return JSON."}]
    )
    assert params["reasoning_effort"] == "none"


def test_structured_retry_preserves_cause_when_correction_is_empty() -> None:
    try:
        structured_result_with_retry(
            RawResult('{"company_name": "Example"}'),
            InterviewPlan,
            EmptyRetryAgent(),
        )
    except ValueError as exc:
        assert "automatic correction call also returned no content" in str(exc).lower()
        assert "valid InterviewPlan data" in str(exc)
    else:
        raise AssertionError("Expected the empty correction call to fail")
