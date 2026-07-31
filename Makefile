.PHONY: install start doctor run api frontend build-frontend cli test lint

install:
	python3 -m pip install -e ".[dev]"

start:
	./scripts/start-local.sh

doctor:
	./scripts/start-local.sh --check-only

run:
	python3 -m uvicorn job_interviewer.api.app:app --host 127.0.0.1 --port 8000

api:
	python3 -m uvicorn job_interviewer.api.app:app --reload --port 8000

frontend:
	cd frontend && npm run dev

build-frontend:
	cd frontend && npm run build

cli:
	job-interviewer --jd-file examples/job_description.txt --candidate-file examples/candidate_profile.txt --output output/interview_report.md

test:
	python3 -m pytest
	cd frontend && npm test -- --run

lint:
	python3 -m ruff check .
	cd frontend && npm run lint
