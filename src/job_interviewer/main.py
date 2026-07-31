"""Command-line interface for the complete interview workflow."""

from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

from job_interviewer.config import Settings
from job_interviewer.documents import extract_document
from job_interviewer.render import render_plan, render_report
from job_interviewer.schemas import WorkflowOptions
from job_interviewer.service import (
    build_interview_plan,
    check_ollama,
    improve_interview_answers,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a local multi-agent job interview preparation workflow."
    )
    parser.add_argument("--jd-file", "--job-file", dest="jd_file", required=True, type=Path)
    parser.add_argument("--candidate-file", required=True, type=Path)
    parser.add_argument("--company", default="", help="Optional company name override.")
    parser.add_argument("--focus", default="balanced company, role, and behavioural coverage")
    parser.add_argument("--role-questions", type=int, default=20, choices=range(1, 21))
    parser.add_argument("--hr-questions", type=int, default=6, choices=range(0, 7))
    parser.add_argument("--iterations", type=int, default=3, choices=range(1, 4))
    parser.add_argument("--pass-score", type=int, default=4, choices=range(1, 6))
    parser.add_argument("--offline", action="store_true", help="Disable company web search.")
    parser.add_argument("--plan-only", action="store_true", help="Skip answer generation.")
    parser.add_argument("--output", type=Path, default=Path("output/interview_report.md"))
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--verbose", action="store_true")
    return parser


def run() -> None:
    load_dotenv()
    args = build_parser().parse_args()
    settings = Settings.from_env()
    status = check_ollama(settings.ollama_base_url, settings.ollama_model)
    if not status.ok:
        raise SystemExit(status.message)

    job_description = extract_document(args.jd_file.name, args.jd_file.read_bytes())
    candidate_profile = extract_document(
        args.candidate_file.name,
        args.candidate_file.read_bytes(),
    )
    options = WorkflowOptions(
        role_question_count=args.role_questions,
        hr_question_count=args.hr_questions,
        max_iterations=args.iterations,
        pass_score=args.pass_score,
        interview_focus=args.focus,
        web_research=not args.offline,
    )
    package = build_interview_plan(
        job_description=job_description,
        candidate_profile=candidate_profile,
        settings=settings,
        options=options,
        company_hint=args.company,
        verbose=args.verbose,
    )
    if args.plan_only:
        artifact = package
        markdown = render_plan(package)
    else:
        artifact = improve_interview_answers(
            package=package,
            candidate_profile=candidate_profile,
            settings=settings,
            verbose=args.verbose,
        )
        markdown = render_report(artifact)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(markdown, encoding="utf-8")
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(artifact.model_dump_json(indent=2), encoding="utf-8")
    print(f"Interview artifact written to {args.output}")


if __name__ == "__main__":
    run()

