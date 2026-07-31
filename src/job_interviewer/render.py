"""Markdown rendering for downloads and CLI output."""

from __future__ import annotations

from job_interviewer.schemas import InterviewPackage, InterviewReport


def render_plan(package: InterviewPackage) -> str:
    research = package.company_research
    analysis = package.jd_analysis
    plan = package.interview_plan
    fit = package.job_fit_metrics
    quality = package.question_quality_metrics
    lines = [
        "# Interview Preparation Plan",
        "",
        f"**Company:** {package.identity.company_name}",
        f"**Role:** {analysis.role_title}",
        f"**Identity confidence:** {package.identity.confidence}",
        "",
        "## Readiness and Quality Metrics",
        "",
        "> These are model-assisted indicators, not hiring probabilities or "
        "ground-truth accuracy.",
        "",
        f"- Overall job fit: **{fit.overall_percent:.1f}%**",
        f"- Must-have fit: **{fit.must_have_percent:.1f}%**",
        f"- Candidate evidence coverage: **{fit.evidence_coverage_percent:.1f}%**",
        f"- Fit assessment confidence: **{fit.assessment_confidence_percent:.1f}%**",
        f"- Question quality: **{quality.overall_quality_percent:.1f}%**",
        f"- JD-grounded questions: **{quality.jd_grounded_percent:.1f}%**",
        f"- Company-grounded questions: **{quality.company_grounded_percent:.1f}%**",
        f"- Duplicate question rate: **{quality.duplicate_rate_percent:.1f}%**",
        "",
        "## Company Research",
        "",
        research.summary,
        "",
    ]
    for fact in research.facts:
        refs = f" ({', '.join(fact.source_ids)})" if fact.source_ids else ""
        lines.append(f"- **{fact.topic}:** {fact.finding}{refs}")
    if research.research_limits:
        lines.extend(["", "### Research Limits", ""])
        lines.extend(f"- {item}" for item in research.research_limits)

    lines.extend(
        [
            "",
            "## JD Analysis",
            "",
            analysis.role_summary,
            "",
            "### Must-Have Skills",
            "",
            *[f"- {item}" for item in analysis.must_have_skills],
            "",
            "### Candidate Strengths",
            "",
            *[f"- {item}" for item in analysis.candidate_strengths],
            "",
            "### Candidate Gaps",
            "",
            *[f"- {item}" for item in analysis.candidate_gaps],
            "",
            "## Interview Questions",
            "",
        ]
    )
    for question in plan.all_questions:
        refs = f" Sources: {', '.join(question.source_ids)}." if question.source_ids else ""
        lines.extend(
            [
                f"### {question.question_id} — {question.category}",
                "",
                question.question,
                "",
                f"**Why it may be asked:** {question.rationale}{refs}",
                "",
                "**Strong-answer signals:**",
                *[f"- {item}" for item in question.strong_answer_signals],
                "",
            ]
        )

    if research.sources:
        lines.extend(["## Sources", ""])
        for source in research.sources:
            date = f" — {source.published}" if source.published else ""
            lines.append(f"- [{source.source_id}] [{source.title}]({source.url}){date}")
    return "\n".join(lines).strip() + "\n"


def render_report(report: InterviewReport) -> str:
    quality = report.answer_quality_metrics
    lines = [
        render_plan(report.package).rstrip(),
        "",
        "## Drafted and Evaluated Answers",
        "",
        f"Evaluation cycles completed: **{report.iterations_completed}** "
        f"(hard maximum: {report.package.options.max_iterations}).",
        "",
        "### Answer Quality Summary",
        "",
        "> These scores are the evaluator agent's rubric-based assessment, not an "
        "independent prediction of interview success.",
        "",
        f"- Average answer score: **{quality.average_score:.2f}/5**",
        f"- Passing rate: **{quality.passing_rate_percent:.1f}%**",
        f"- Evidence usage: **{quality.evidence_usage_percent:.1f}%**",
        f"- Unsupported-claim rate: "
        f"**{quality.unsupported_claim_rate_percent:.1f}%**",
        f"- Answers still needing improvement: "
        f"**{quality.answers_needing_improvement}**",
        "",
    ]
    questions = {
        question.question_id: question
        for question in report.package.interview_plan.all_questions
    }
    evaluations = {
        evaluation.question_id: evaluation for evaluation in report.evaluations
    }
    for answer in report.answers:
        question = questions[answer.question_id]
        evaluation = evaluations.get(answer.question_id)
        lines.extend(
            [
                f"### {answer.question_id} — {question.category}",
                "",
                f"**Question:** {question.question}",
                "",
                f"**Suggested answer (revision {answer.revision}):**",
                "",
                answer.answer,
                "",
            ]
        )
        if evaluation:
            lines.extend(
                [
                    f"**Final score:** {evaluation.score}/5",
                    "",
                    "**Strengths:**",
                    *[f"- {item}" for item in evaluation.strengths],
                    "",
                    "**Remaining improvements:**",
                    *[f"- {item}" for item in evaluation.improvement_instructions],
                    "",
                ]
            )
            if evaluation.unsupported_claims:
                lines.extend(
                    [
                        "**Unsupported claims detected:**",
                        *[f"- {item}" for item in evaluation.unsupported_claims],
                        "",
                    ]
                )
        if answer.evidence_used:
            lines.extend(
                [
                    f"**Candidate evidence IDs used:** {', '.join(answer.evidence_used)}",
                    "",
                ]
            )
        if answer.missing_evidence:
            lines.extend(
                [
                    "**Evidence still needed:**",
                    *[f"- {item}" for item in answer.missing_evidence],
                    "",
                ]
            )
    lines.extend(["## Iteration History", ""])
    for item in report.iteration_history:
        lines.append(
            f"- Cycle {item.iteration}: evaluated {item.evaluated_count}, "
            f"revised {item.revised_count}, passing {item.passing_count}."
        )
    return "\n".join(lines).strip() + "\n"
