from interview_local.schemas import (
    InterviewPlan,
    InterviewQuestion,
    JDAnalysis,
    RequirementAssessment,
    WorkflowOptions,
)


def question(text: str, group: str = "role_company") -> InterviewQuestion:
    return InterviewQuestion(
        question_id="wrong",
        group=group,
        category="Test",
        question=text,
        rationale="Reason",
    )


def test_workflow_options_enforce_hard_limits() -> None:
    options = WorkflowOptions(role_question_count=20, hr_question_count=6, max_iterations=3)
    assert options.role_question_count == 20
    assert options.hr_question_count == 6
    assert options.max_iterations == 3


def test_plan_normalization_deduplicates_and_caps() -> None:
    plan = InterviewPlan(
        company_name="Example",
        role_title="Engineer",
        role_company_questions=[
            question("Why this role?"),
            question("Why this role?"),
            question("Describe the system."),
        ],
        hr_questions=[question("What is your strength?", "hr")],
    )

    plan.normalized(role_limit=1, hr_limit=1)

    assert [item.question_id for item in plan.all_questions] == ["RC01", "HR01"]
    assert plan.role_company_questions[0].group == "role_company"
    assert plan.hr_questions[0].group == "hr"


def test_plan_derives_groups_and_missing_ids_from_question_containers() -> None:
    plan = InterviewPlan.model_validate(
        {
            "company_name": "Example",
            "role_title": "Engineer",
            "role_company_questions": [
                {
                    "group": "role_company_questions",
                    "category": "Role",
                    "question": "How would you design the platform?",
                    "rationale": "Assess design skills.",
                }
            ],
            "hr_questions": [
                {
                    "question_id": "HR_01",
                    "group": "hr_questions",
                    "category": "Behavioural",
                    "question": "Tell me about a difficult stakeholder.",
                    "rationale": "Assess communication.",
                }
            ],
        }
    )

    assert plan.role_company_questions[0].group == "role_company"
    assert plan.role_company_questions[0].question_id == "RC01"
    assert plan.hr_questions[0].group == "hr"


def test_jd_analysis_normalizes_small_model_skill_objects() -> None:
    analysis = JDAnalysis.model_validate(
        {
            "role_title": "Engineer",
            "role_summary": "Build services.",
            "must_have_skills": [
                {"requirement": "Python", "status": "matched"},
                "SQL",
            ],
        }
    )

    assert analysis.must_have_skills == ["Python", "SQL"]


def test_requirement_assessment_normalizes_semantic_aliases() -> None:
    assessment = RequirementAssessment.model_validate(
        {
            "requirement": "Data lake design",
            "category": "preferred_skill",
            "status": "partial match",
            "confidence": 75,
        }
    )

    assert assessment.category == "preferred"
    assert assessment.status == "partial"
    assert assessment.confidence == 0.75


def test_requirement_assessment_normalizes_plural_category_aliases() -> None:
    expected_categories = {
        "required_skills": "must_have",
        "must have skills": "must_have",
        "preferred_skills": "preferred",
        "nice-to-have skills": "preferred",
        "behavioral competencies": "competency",
        "soft_skills": "competency",
    }

    for model_category, expected in expected_categories.items():
        assessment = RequirementAssessment.model_validate(
            {
                "requirement": "Example requirement",
                "category": model_category,
                "status": "matched",
            }
        )
        assert assessment.category == expected
