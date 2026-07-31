"""Typed contracts shared by crews, flows, the CLI, and the web app."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


def _string_list(value: object) -> object:
    """Normalize common small-model list variants without inventing content."""
    if value is None:
        return []
    if not isinstance(value, list):
        return value
    normalized: list[str] = []
    preferred_keys = (
        "requirement",
        "finding",
        "topic",
        "skill",
        "name",
        "text",
        "value",
        "evidence",
    )
    for item in value:
        if isinstance(item, str):
            if item.strip():
                normalized.append(item.strip())
            continue
        if isinstance(item, dict):
            candidate = next(
                (
                    item[key]
                    for key in preferred_keys
                    if isinstance(item.get(key), str) and item[key].strip()
                ),
                None,
            )
            if candidate:
                normalized.append(candidate)
    return normalized


class WorkflowOptions(BaseModel):
    role_question_count: int = Field(default=20, ge=1, le=20)
    hr_question_count: int = Field(default=6, ge=0, le=6)
    max_iterations: int = Field(default=3, ge=1, le=3)
    pass_score: int = Field(default=4, ge=1, le=5)
    answer_word_limit: int = Field(default=180, ge=60, le=300)
    interview_focus: str = "balanced company, role, technical, and behavioural coverage"
    web_research: bool = True
    search_region: str = "sg-en"


class JobIdentity(BaseModel):
    company_name: str = "Unknown company"
    role_title: str = "Unknown role"
    confidence: Literal["high", "medium", "low"] = "low"
    evidence: str = ""


class SearchSource(BaseModel):
    source_id: str
    title: str
    url: str
    snippet: str
    published: str = ""


class SearchBundle(BaseModel):
    company_name: str
    searched_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    sources: list[SearchSource] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CompanyFact(BaseModel):
    topic: str
    finding: str
    source_ids: list[str] = Field(default_factory=list)

    @field_validator("source_ids", mode="before")
    @classmethod
    def normalize_source_ids(cls, value: object) -> object:
        return _string_list(value)


class CompanyResearch(BaseModel):
    company_name: str
    summary: str
    facts: list[CompanyFact] = Field(default_factory=list)
    interview_talking_points: list[str] = Field(default_factory=list)
    research_limits: list[str] = Field(default_factory=list)
    sources: list[SearchSource] = Field(default_factory=list)

    @field_validator("interview_talking_points", "research_limits", mode="before")
    @classmethod
    def normalize_text_lists(cls, value: object) -> object:
        return _string_list(value)


RequirementCategory = Literal["must_have", "preferred", "competency"]
MatchStatus = Literal["matched", "partial", "gap", "unknown"]


class RequirementAssessment(BaseModel):
    """A candidate-to-JD mapping used to calculate a transparent fit score."""

    requirement: str
    category: RequirementCategory
    status: MatchStatus
    evidence: str = ""
    confidence: float = Field(default=0.5, ge=0, le=1)

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
        aliases = {
            "must": "must_have",
            "required": "must_have",
            "required_skill": "must_have",
            "required_skills": "must_have",
            "mandatory": "must_have",
            "mandatory_skill": "must_have",
            "mandatory_skills": "must_have",
            "core": "must_have",
            "must_have_skill": "must_have",
            "must_have_skills": "must_have",
            "preferred_skill": "preferred",
            "preferred_skills": "preferred",
            "nice_to_have": "preferred",
            "nice_to_have_skill": "preferred",
            "nice_to_have_skills": "preferred",
            "desirable": "preferred",
            "behavioral": "competency",
            "behavioural": "competency",
            "behavioral_competency": "competency",
            "behavioral_competencies": "competency",
            "behavioural_competency": "competency",
            "behavioural_competencies": "competency",
            "soft_skill": "competency",
            "soft_skills": "competency",
            "competencies": "competency",
        }
        return aliases.get(normalized, normalized)

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
        aliases = {
            "match": "matched",
            "full_match": "matched",
            "strong_match": "matched",
            "partially_matched": "partial",
            "partial_match": "partial",
            "some_evidence": "partial",
            "missing": "gap",
            "not_matched": "gap",
            "no_evidence": "gap",
            "insufficient_evidence": "unknown",
            "unclear": "unknown",
        }
        return aliases.get(normalized, normalized)

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, value: object) -> object:
        if isinstance(value, (int, float)) and 1 < value <= 100:
            return value / 100
        return value


class JDAnalysis(BaseModel):
    role_title: str
    seniority: str = "Not specified"
    role_summary: str
    responsibilities: list[str] = Field(default_factory=list)
    must_have_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    competencies: list[str] = Field(default_factory=list)
    likely_challenges: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    candidate_strengths: list[str] = Field(default_factory=list)
    candidate_gaps: list[str] = Field(default_factory=list)
    requirement_assessments: list[RequirementAssessment] = Field(default_factory=list)

    @field_validator(
        "responsibilities",
        "must_have_skills",
        "preferred_skills",
        "competencies",
        "likely_challenges",
        "keywords",
        "candidate_strengths",
        "candidate_gaps",
        mode="before",
    )
    @classmethod
    def normalize_text_lists(cls, value: object) -> object:
        return _string_list(value)


QuestionGroup = Literal["role_company", "hr"]


class InterviewQuestion(BaseModel):
    question_id: str
    group: QuestionGroup
    category: str
    question: str
    rationale: str
    strong_answer_signals: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)

    @field_validator("strong_answer_signals", "source_ids", mode="before")
    @classmethod
    def normalize_text_lists(cls, value: object) -> object:
        return _string_list(value)


class InterviewPlan(BaseModel):
    company_name: str
    role_title: str
    role_company_questions: list[InterviewQuestion] = Field(default_factory=list)
    hr_questions: list[InterviewQuestion] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def derive_question_groups_from_containers(cls, value: object) -> object:
        """Treat each question array as authoritative for its group and initial ID."""
        if not isinstance(value, dict):
            return value

        normalized = dict(value)
        for field_name, group, prefix in (
            ("role_company_questions", "role_company", "RC"),
            ("hr_questions", "hr", "HR"),
        ):
            questions = normalized.get(field_name)
            if not isinstance(questions, list):
                continue
            normalized_questions: list[object] = []
            for index, question in enumerate(questions, start=1):
                if not isinstance(question, dict):
                    normalized_questions.append(question)
                    continue
                normalized_question = dict(question)
                normalized_question["group"] = group
                normalized_question.setdefault("question_id", f"{prefix}{index:02d}")
                normalized_questions.append(normalized_question)
            normalized[field_name] = normalized_questions
        return normalized

    @property
    def all_questions(self) -> list[InterviewQuestion]:
        return [*self.role_company_questions, *self.hr_questions]

    def normalized(self, role_limit: int, hr_limit: int) -> InterviewPlan:
        """Enforce stable IDs, groups, uniqueness, and hard question ceilings."""
        seen: set[str] = set()

        def clean(
            questions: list[InterviewQuestion],
            group: QuestionGroup,
            prefix: str,
            limit: int,
        ) -> list[InterviewQuestion]:
            result: list[InterviewQuestion] = []
            for question in questions:
                key = " ".join(question.question.lower().split())
                if not key or key in seen:
                    continue
                seen.add(key)
                question.group = group
                question.question_id = f"{prefix}{len(result) + 1:02d}"
                result.append(question)
                if len(result) >= limit:
                    break
            return result

        self.role_company_questions = clean(
            self.role_company_questions,
            "role_company",
            "RC",
            role_limit,
        )
        self.hr_questions = clean(self.hr_questions, "hr", "HR", hr_limit)
        return self


class AnswerDraft(BaseModel):
    question_id: str
    answer: str
    evidence_used: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    revision: int = Field(default=0, ge=0, le=3)

    @field_validator("evidence_used", "missing_evidence", mode="before")
    @classmethod
    def normalize_text_lists(cls, value: object) -> object:
        return _string_list(value)


class AnswerSet(BaseModel):
    answers: list[AnswerDraft] = Field(default_factory=list)


class AnswerEvaluation(BaseModel):
    question_id: str
    score: int = Field(ge=1, le=5)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    improvement_instructions: list[str] = Field(default_factory=list)

    @field_validator(
        "strengths",
        "weaknesses",
        "unsupported_claims",
        "improvement_instructions",
        mode="before",
    )
    @classmethod
    def normalize_text_lists(cls, value: object) -> object:
        return _string_list(value)


class EvaluationSet(BaseModel):
    evaluations: list[AnswerEvaluation] = Field(default_factory=list)


class JobFitMetrics(BaseModel):
    """Model-assisted fit indicators; these are not hiring-outcome accuracy."""

    overall_percent: float = Field(default=0, ge=0, le=100)
    must_have_percent: float = Field(default=0, ge=0, le=100)
    preferred_percent: float = Field(default=0, ge=0, le=100)
    competency_percent: float = Field(default=0, ge=0, le=100)
    evidence_coverage_percent: float = Field(default=0, ge=0, le=100)
    assessment_confidence_percent: float = Field(default=0, ge=0, le=100)
    matched_count: int = 0
    partial_count: int = 0
    gap_count: int = 0
    unknown_count: int = 0
    assessed_count: int = 0


class QuestionQualityMetrics(BaseModel):
    total_questions: int = 0
    role_company_questions: int = 0
    hr_questions: int = 0
    jd_grounded_percent: float = Field(default=0, ge=0, le=100)
    company_grounded_percent: float = Field(default=0, ge=0, le=100)
    rationale_coverage_percent: float = Field(default=0, ge=0, le=100)
    answer_signal_coverage_percent: float = Field(default=0, ge=0, le=100)
    duplicate_rate_percent: float = Field(default=0, ge=0, le=100)
    category_diversity: int = 0
    overall_quality_percent: float = Field(default=0, ge=0, le=100)


class AnswerQualityMetrics(BaseModel):
    answered_count: int = 0
    evaluated_count: int = 0
    average_score: float = Field(default=0, ge=0, le=5)
    score_percent: float = Field(default=0, ge=0, le=100)
    passing_rate_percent: float = Field(default=0, ge=0, le=100)
    evidence_usage_percent: float = Field(default=0, ge=0, le=100)
    unsupported_claim_rate_percent: float = Field(default=0, ge=0, le=100)
    answers_needing_improvement: int = 0


class InterviewPackage(BaseModel):
    identity: JobIdentity
    company_research: CompanyResearch
    jd_analysis: JDAnalysis
    interview_plan: InterviewPlan
    options: WorkflowOptions
    job_fit_metrics: JobFitMetrics = Field(default_factory=JobFitMetrics)
    question_quality_metrics: QuestionQualityMetrics = Field(
        default_factory=QuestionQualityMetrics
    )
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class IterationSummary(BaseModel):
    iteration: int = Field(ge=1, le=3)
    evaluated_count: int = 0
    revised_count: int = 0
    passing_count: int = 0


class InterviewReport(BaseModel):
    package: InterviewPackage
    answers: list[AnswerDraft]
    evaluations: list[AnswerEvaluation]
    iterations_completed: int = Field(ge=1, le=3)
    stopped_early: bool = False
    iteration_history: list[IterationSummary] = Field(default_factory=list)
    answer_quality_metrics: AnswerQualityMetrics = Field(
        default_factory=AnswerQualityMetrics
    )
    generated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    @model_validator(mode="after")
    def question_ids_are_known(self) -> InterviewReport:
        known = {question.question_id for question in self.package.interview_plan.all_questions}
        unknown = {answer.question_id for answer in self.answers} - known
        if unknown:
            raise ValueError(f"Answers reference unknown question IDs: {sorted(unknown)}")
        return self


class AnswerFlowState(BaseModel):
    package: InterviewPackage | None = None
    candidate_profile: str = ""
    selected_question_ids: list[str] = Field(default_factory=list)
    answers: list[AnswerDraft] = Field(default_factory=list)
    evaluations: list[AnswerEvaluation] = Field(default_factory=list)
    iterations_completed: int = 0
    stopped_early: bool = False
    iteration_history: list[IterationSummary] = Field(default_factory=list)

    @field_validator("selected_question_ids")
    @classmethod
    def deduplicate_ids(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(values))
