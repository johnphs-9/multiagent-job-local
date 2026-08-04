from interview_local.answer_flow import AnswerImprovementFlow, CrewAIAnswerRunner
from interview_local.config import Settings
from interview_local.schemas import (
    AnswerDraft,
    AnswerEvaluation,
    CompanyResearch,
    InterviewPackage,
    InterviewPlan,
    InterviewQuestion,
    JDAnalysis,
    JobIdentity,
    WorkflowOptions,
)


def package(max_iterations: int = 3, pass_score: int = 4) -> InterviewPackage:
    question = InterviewQuestion(
        question_id="RC01",
        group="role_company",
        category="Role",
        question="Why are you suitable?",
        rationale="Tests fit.",
    )
    return InterviewPackage(
        identity=JobIdentity(company_name="Example", role_title="Engineer"),
        company_research=CompanyResearch(company_name="Example", summary="Summary"),
        jd_analysis=JDAnalysis(
            role_title="Engineer",
            role_summary="Build systems.",
        ),
        interview_plan=InterviewPlan(
            company_name="Example",
            role_title="Engineer",
            role_company_questions=[question],
        ),
        options=WorkflowOptions(
            role_question_count=1,
            hr_question_count=0,
            max_iterations=max_iterations,
            pass_score=pass_score,
        ),
    )


class FakeRunner:
    def __init__(self, score: int) -> None:
        self.score = score
        self.evaluation_calls = 0
        self.revision_calls = 0

    def draft(self, questions, candidate_profile, word_limit):
        return [AnswerDraft(question_id="RC01", answer="Initial evidence.")]

    def evaluate(self, questions, answers, candidate_profile):
        self.evaluation_calls += 1
        return [AnswerEvaluation(question_id="RC01", score=self.score)]

    def revise(
        self,
        questions,
        answers,
        evaluations,
        candidate_profile,
        word_limit,
        revision,
    ):
        self.revision_calls += 1
        return [
            AnswerDraft(
                question_id="RC01",
                answer=f"Revision {revision}.",
                revision=revision,
            )
        ]


def test_flow_never_exceeds_three_evaluation_cycles() -> None:
    runner = FakeRunner(score=1)
    flow = AnswerImprovementFlow(Settings(), runner=runner)

    result = flow.kickoff(
        inputs={
            "package": package().model_dump(mode="json"),
            "candidate_profile": "Verified experience.",
            "selected_question_ids": ["RC01"],
        }
    )

    assert result.iterations_completed == 3
    assert runner.evaluation_calls == 3
    assert runner.revision_calls == 2


def test_flow_stops_early_when_answers_pass() -> None:
    runner = FakeRunner(score=4)
    flow = AnswerImprovementFlow(Settings(), runner=runner)

    result = flow.kickoff(
        inputs={
            "package": package().model_dump(mode="json"),
            "candidate_profile": "Verified experience.",
            "selected_question_ids": ["RC01"],
        }
    )

    assert result.iterations_completed == 1
    assert result.stopped_early
    assert runner.revision_calls == 0


def test_unsafe_evaluator_advice_is_removed() -> None:
    evaluations = [
        AnswerEvaluation(
            question_id="RC01",
            score=2,
            improvement_instructions=[
                "Invent a plausible situation with a better result.",
                "Explain the verified metric more clearly.",
            ],
        )
    ]

    cleaned = CrewAIAnswerRunner._remove_unsafe_coaching(evaluations)

    assert all(
        "invent" not in instruction.lower()
        for instruction in cleaned[0].improvement_instructions
    )
    assert any(
        "genuine example" in instruction
        for instruction in cleaned[0].improvement_instructions
    )
