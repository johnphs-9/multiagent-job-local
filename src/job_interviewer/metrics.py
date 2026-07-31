"""Deterministic metrics calculated from the agents' structured outputs."""

from __future__ import annotations

from collections import Counter

from job_interviewer.schemas import (
    AnswerDraft,
    AnswerEvaluation,
    AnswerQualityMetrics,
    InterviewPlan,
    JDAnalysis,
    JobFitMetrics,
    QuestionQualityMetrics,
    RequirementAssessment,
)


def _percent(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return round(100 * numerator / denominator, 1)


def _fit_for(
    assessments: list[RequirementAssessment],
    category: str,
) -> float:
    selected = [item for item in assessments if item.category == category]
    values = {"matched": 1.0, "partial": 0.5, "gap": 0.0, "unknown": 0.0}
    return _percent(
        sum(values[item.status] for item in selected),
        len(selected),
    )


def calculate_job_fit(analysis: JDAnalysis) -> JobFitMetrics:
    """Score explicit requirement mappings, weighting must-haves most heavily."""
    assessments = analysis.requirement_assessments
    must_have = _fit_for(assessments, "must_have")
    preferred = _fit_for(assessments, "preferred")
    competency = _fit_for(assessments, "competency")

    available = [
        (must_have, 0.7, any(item.category == "must_have" for item in assessments)),
        (preferred, 0.2, any(item.category == "preferred" for item in assessments)),
        (competency, 0.1, any(item.category == "competency" for item in assessments)),
    ]
    active_weight = sum(weight for _, weight, present in available if present)
    overall = (
        sum(value * weight for value, weight, present in available if present)
        / active_weight
        if active_weight
        else 0
    )
    counts = Counter(item.status for item in assessments)
    evidenced = sum(
        bool(item.evidence.strip()) and item.status in {"matched", "partial"}
        for item in assessments
    )
    confidence = (
        sum(item.confidence for item in assessments) / len(assessments)
        if assessments
        else 0
    )
    return JobFitMetrics(
        overall_percent=round(overall, 1),
        must_have_percent=must_have,
        preferred_percent=preferred,
        competency_percent=competency,
        evidence_coverage_percent=_percent(evidenced, len(assessments)),
        assessment_confidence_percent=round(confidence * 100, 1),
        matched_count=counts["matched"],
        partial_count=counts["partial"],
        gap_count=counts["gap"],
        unknown_count=counts["unknown"],
        assessed_count=len(assessments),
    )


def interpret_job_fit(metrics: JobFitMetrics) -> tuple[str, str]:
    """Return a cautious readiness band and an evidence-aware interpretation."""
    if metrics.assessed_count == 0:
        return (
            "Not assessed",
            "No requirement-level mappings were returned. Rebuild the plan or review "
            "the JD and candidate profile manually.",
        )
    if metrics.overall_percent >= 80:
        label = "Strong documented alignment"
        summary = (
            "The supplied profile directly or partially supports most weighted requirements."
        )
    elif metrics.overall_percent >= 65:
        label = "Promising alignment"
        summary = (
            "The supplied profile supports many requirements, with some gaps to prepare for."
        )
    elif metrics.overall_percent >= 50:
        label = "Partial alignment"
        summary = (
            "Relevant evidence exists, but several requirements need stronger examples "
            "or development."
        )
    else:
        label = "Material documented gaps"
        summary = (
            "The supplied profile currently supports fewer than half of the weighted "
            "requirements."
        )

    cautions: list[str] = []
    if metrics.must_have_percent < 60:
        cautions.append("Must-have coverage is low, so prioritize those gaps.")
    if metrics.evidence_coverage_percent < 60:
        cautions.append(
            "Evidence coverage is limited; adding verified CV details may change the score."
        )
    if metrics.assessment_confidence_percent < 60:
        cautions.append(
            "Assessment confidence is low because the JD or candidate evidence is ambiguous."
        )
    if metrics.unknown_count:
        cautions.append(
            f"{metrics.unknown_count} requirement(s) could not be assessed from the supplied data."
        )
    return label, " ".join([summary, *cautions])


def calculate_question_quality(plan: InterviewPlan) -> QuestionQualityMetrics:
    """Measure grounding and completeness without asking another LLM."""
    questions = plan.all_questions
    total = len(questions)
    normalized = [" ".join(item.question.lower().split()) for item in questions]
    unique = len(set(normalized))
    jd_grounded = sum("JD" in item.source_ids for item in questions)
    role_questions = plan.role_company_questions
    company_grounded = sum(
        any(source.startswith("S") for source in item.source_ids)
        for item in role_questions
    )
    rationale = sum(bool(item.rationale.strip()) for item in questions)
    answer_signals = sum(bool(item.strong_answer_signals) for item in questions)
    categories = len({item.category.strip().lower() for item in questions if item.category})

    jd_grounding = _percent(jd_grounded, total)
    company_grounding = _percent(company_grounded, len(role_questions))
    grounding = (jd_grounding + company_grounding) / 2
    rationale_coverage = _percent(rationale, total)
    signal_coverage = _percent(answer_signals, total)
    duplicate_rate = _percent(total - unique, total)
    diversity_target = min(6, total)
    diversity = _percent(min(categories, diversity_target), diversity_target)
    overall = (
        0.35 * grounding
        + 0.2 * rationale_coverage
        + 0.25 * signal_coverage
        + 0.1 * (100 - duplicate_rate)
        + 0.1 * diversity
    )
    return QuestionQualityMetrics(
        total_questions=total,
        role_company_questions=len(plan.role_company_questions),
        hr_questions=len(plan.hr_questions),
        jd_grounded_percent=jd_grounding,
        company_grounded_percent=company_grounding,
        rationale_coverage_percent=rationale_coverage,
        answer_signal_coverage_percent=signal_coverage,
        duplicate_rate_percent=duplicate_rate,
        category_diversity=categories,
        overall_quality_percent=round(overall, 1) if total else 0,
    )


def calculate_answer_quality(
    answers: list[AnswerDraft],
    evaluations: list[AnswerEvaluation],
    pass_score: int,
) -> AnswerQualityMetrics:
    """Aggregate the evaluator's final per-answer scores and evidence checks."""
    evaluated = len(evaluations)
    average = (
        sum(item.score for item in evaluations) / evaluated if evaluated else 0
    )
    passing = sum(item.score >= pass_score for item in evaluations)
    unsupported = sum(bool(item.unsupported_claims) for item in evaluations)
    evidence_used = sum(bool(item.evidence_used) for item in answers)
    return AnswerQualityMetrics(
        answered_count=len(answers),
        evaluated_count=evaluated,
        average_score=round(average, 2),
        score_percent=round(average * 20, 1),
        passing_rate_percent=_percent(passing, evaluated),
        evidence_usage_percent=_percent(evidence_used, len(answers)),
        unsupported_claim_rate_percent=_percent(unsupported, evaluated),
        answers_needing_improvement=evaluated - passing,
    )
