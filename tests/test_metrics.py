from job_interviewer.metrics import (
    calculate_answer_quality,
    calculate_job_fit,
    calculate_question_quality,
    interpret_job_fit,
)
from job_interviewer.schemas import (
    AnswerDraft,
    AnswerEvaluation,
    InterviewPlan,
    InterviewQuestion,
    JDAnalysis,
    RequirementAssessment,
)


def test_job_fit_weights_requirement_categories() -> None:
    analysis = JDAnalysis(
        role_title="Engineer",
        role_summary="Build systems.",
        requirement_assessments=[
            RequirementAssessment(
                requirement="Python",
                category="must_have",
                status="matched",
                evidence="Built a Python service.",
                confidence=0.9,
            ),
            RequirementAssessment(
                requirement="Cloud",
                category="must_have",
                status="partial",
                evidence="Completed a cloud project.",
                confidence=0.7,
            ),
            RequirementAssessment(
                requirement="Mentoring",
                category="competency",
                status="gap",
                confidence=0.8,
            ),
        ],
    )

    metrics = calculate_job_fit(analysis)

    assert metrics.must_have_percent == 75.0
    assert metrics.competency_percent == 0.0
    assert metrics.overall_percent == 65.6
    assert metrics.evidence_coverage_percent == 66.7


def test_question_quality_measures_grounding_and_duplicates() -> None:
    plan = InterviewPlan(
        company_name="Example",
        role_title="Engineer",
        role_company_questions=[
            InterviewQuestion(
                question_id="RC01",
                group="role_company",
                category="Technical",
                question="How would you design the service?",
                rationale="Tests system design.",
                strong_answer_signals=["Trade-offs"],
                source_ids=["JD", "S1"],
            ),
            InterviewQuestion(
                question_id="RC02",
                group="role_company",
                category="Technical",
                question="How would you design the service?",
                rationale="Tests system design.",
                strong_answer_signals=["Trade-offs"],
                source_ids=["JD"],
            ),
        ],
    )

    metrics = calculate_question_quality(plan)

    assert metrics.jd_grounded_percent == 100.0
    assert metrics.company_grounded_percent == 50.0
    assert metrics.duplicate_rate_percent == 50.0
    assert metrics.category_diversity == 1


def test_answer_quality_aggregates_final_evaluations() -> None:
    answers = [
        AnswerDraft(question_id="RC01", answer="A", evidence_used=["E1"]),
        AnswerDraft(question_id="RC02", answer="B"),
    ]
    evaluations = [
        AnswerEvaluation(question_id="RC01", score=4),
        AnswerEvaluation(
            question_id="RC02",
            score=2,
            unsupported_claims=["Unsupported claim"],
        ),
    ]

    metrics = calculate_answer_quality(answers, evaluations, pass_score=4)

    assert metrics.average_score == 3
    assert metrics.passing_rate_percent == 50.0
    assert metrics.evidence_usage_percent == 50.0
    assert metrics.unsupported_claim_rate_percent == 50.0
    assert metrics.answers_needing_improvement == 1


def test_job_fit_interpretation_flags_low_evidence() -> None:
    analysis = JDAnalysis(
        role_title="Engineer",
        role_summary="Build systems.",
        requirement_assessments=[
            RequirementAssessment(
                requirement="Python",
                category="must_have",
                status="partial",
                confidence=0.4,
            )
        ],
    )
    metrics = calculate_job_fit(analysis)

    label, assessment = interpret_job_fit(metrics)

    assert label == "Partial alignment"
    assert "Evidence coverage is limited" in assessment
    assert "Assessment confidence is low" in assessment
