#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"
VENV_PYTHON="${PROJECT_ROOT}/.venv/bin/python"
# Prefer this checkout over any stale editable install recorded in the virtual
# environment. This also makes python-dotenv discover this checkout's .env.
export PYTHONPATH="${PROJECT_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"
APP_HOST="${APP_HOST:-127.0.0.1}"
APP_PORT="${APP_PORT:-8000}"
STARTUP_TIMEOUT_SECONDS="${STARTUP_TIMEOUT_SECONDS:-30}"
CHECK_ONLY=false
OLLAMA_PID=""
OLLAMA_LOG="${PROJECT_ROOT}/output/ollama-serve.log"

pass() {
    printf '[x] %s\n' "$1"
}

pending() {
    printf '[ ] %s\n' "$1" >&2
}

fail() {
    pending "$1"
    if [[ $# -gt 1 ]]; then
        printf '    %s\n' "$2" >&2
    fi
    exit 1
}

usage() {
    cat <<'EOF'
Usage: scripts/start-local.sh [--check-only] [--help]

Checks the local macOS or WSL2 environment, starts Ollama when needed, builds the
React frontend, and runs Uvicorn in the foreground with visible server output.

Options:
  --check-only  Run checks without building or starting missing processes.
  --help        Show this help text.

Optional environment values:
  APP_HOST                 Uvicorn host (default: 127.0.0.1)
  APP_PORT                 Uvicorn port (default: 8000)
  STARTUP_TIMEOUT_SECONDS  Service startup timeout (default: 30)
EOF
}

cleanup() {
    local exit_code=$?
    trap - EXIT INT TERM HUP

    if [[ -n "${OLLAMA_PID}" ]] && kill -0 "${OLLAMA_PID}" 2>/dev/null; then
        kill "${OLLAMA_PID}" 2>/dev/null || true
        wait "${OLLAMA_PID}" 2>/dev/null || true
        pass "Stopped launcher-managed Ollama process ${OLLAMA_PID}"
    fi

    exit "${exit_code}"
}

http_ok() {
    local url=$1
    "${VENV_PYTHON}" - "${url}" <<'PY' >/dev/null 2>&1
import sys
from urllib.request import urlopen

with urlopen(sys.argv[1], timeout=2) as response:
    if response.status >= 400:
        raise SystemExit(1)
PY
}

port_open() {
    local host=$1
    local port=$2
    "${VENV_PYTHON}" - "${host}" "${port}" <<'PY' >/dev/null 2>&1
import socket
import sys

try:
    with socket.create_connection((sys.argv[1], int(sys.argv[2])), timeout=1):
        pass
except OSError:
    raise SystemExit(1)
PY
}

wait_for_url() {
    local url=$1
    local waited=0
    while (( waited < STARTUP_TIMEOUT_SECONDS )); do
        if http_ok "${url}"; then
            return 0
        fi
        sleep 1
        waited=$((waited + 1))
    done
    return 1
}

check_node_version() {
    local version major minor
    version="$(node --version)"
    version="${version#v}"
    major="${version%%.*}"
    version="${version#*.}"
    minor="${version%%.*}"

    if (( major == 20 && minor >= 19 )); then
        return 0
    fi
    if (( major == 22 && minor >= 12 )); then
        return 0
    fi
    if (( major > 22 )); then
        return 0
    fi
    return 1
}

for argument in "$@"; do
    case "${argument}" in
        --check-only)
            CHECK_ONLY=true
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            usage >&2
            fail "Recognised command-line arguments" "Unknown argument: ${argument}"
            ;;
    esac
done

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP

cd "${PROJECT_ROOT}"

case "$(uname -s)" in
    Darwin)
        PLATFORM="macOS"
        ;;
    Linux)
        if [[ -r /proc/version ]] && grep -qiE 'microsoft|wsl' /proc/version; then
            PLATFORM="WSL2"
        else
            fail "Supported operating system detected" \
                "This launcher supports macOS and WSL2."
        fi
        ;;
    *)
        fail "Supported operating system detected" \
            "This launcher supports macOS and WSL2."
        ;;
esac
pass "Supported operating system detected: ${PLATFORM}"

[[ "${APP_PORT}" =~ ^[0-9]+$ ]] && (( APP_PORT >= 1 && APP_PORT <= 65535 )) \
    || fail "Application port is valid" "APP_PORT must be between 1 and 65535."
pass "Application port is valid: ${APP_PORT}"

command -v python3 >/dev/null 2>&1 \
    || fail "Python 3 command is available" "Install Python 3.10 through 3.13."
pass "Python 3 command is available: $(command -v python3)"

[[ -x "${VENV_PYTHON}" ]] \
    || fail "Project virtual environment is available" \
        "Create it with: python3 -m venv .venv"
pass "Project virtual environment is available: ${VENV_PYTHON}"

"${VENV_PYTHON}" -c \
    'import sys; raise SystemExit(not ((3, 10) <= sys.version_info[:2] < (3, 14)))' \
    || fail "Virtual-environment Python version is supported" \
        "Recreate .venv with Python 3.10 through 3.13."
pass "Virtual-environment Python version is supported: $("${VENV_PYTHON}" -c 'import platform; print(platform.python_version())')"

if ! "${VENV_PYTHON}" - <<'PY' >/dev/null 2>&1
import crewai
import ddgs
import docx
import dotenv
import fastapi
import json_repair
import multipart
import pypdf
import uvicorn
import interview_local
PY
then
    fail "Python application dependencies are installed" \
        'Install them with: .venv/bin/python -m pip install -e ".[dev]"'
fi
pass "Python application dependencies are installed"

RESOLVED_SOURCE="$("${VENV_PYTHON}" - <<'PY'
from pathlib import Path

import interview_local

print(Path(interview_local.__file__).resolve())
PY
)"
case "${RESOLVED_SOURCE}" in
    "${PROJECT_ROOT}/src/interview_local/"*)
        pass "Python application source resolved from this checkout"
        ;;
    *)
        fail "Python application source resolved from this checkout" \
            "Resolved interview_local from ${RESOLVED_SOURCE}"
        ;;
esac

command -v node >/dev/null 2>&1 \
    || fail "Node.js is available" "Install Node.js 20.19+ or 22.12+."
check_node_version \
    || fail "Node.js version is supported" \
        "Install Node.js 20.19+ or 22.12+; the current version is $(node --version)."
pass "Node.js version is supported: $(node --version)"

command -v npm >/dev/null 2>&1 \
    || fail "npm is available" "Install npm with a supported Node.js release."
pass "npm is available: $(npm --version)"

npm --prefix "${FRONTEND_DIR}" ls --depth=0 >/dev/null 2>&1 \
    || fail "Frontend dependencies are installed" \
        "Install them with: npm install --prefix frontend"
pass "Frontend dependencies are installed"

if [[ "${CHECK_ONLY}" == true ]]; then
    [[ -f "${FRONTEND_DIR}/dist/index.html" ]] \
        || fail "Compiled frontend is available" \
            "Build it with: npm run build --prefix frontend"
    pass "Compiled frontend is available"
else
    if ! npm --prefix "${FRONTEND_DIR}" run build; then
        fail "Frontend production build completed" \
            "Resolve the TypeScript or Vite build errors shown above."
    fi
    pass "Frontend production build completed"
fi

if [[ -f "${PROJECT_ROOT}/.env" ]]; then
    pass "Local .env configuration is available"
else
    pass "Local .env is optional; built-in defaults will be used"
fi

if ! CONFIG_SUMMARY="$("${VENV_PYTHON}" - <<'PY'
from interview_local.config import Settings

settings = Settings.from_env()
print(settings.model_profile)
print(settings.ollama_base_url.rstrip("/"))
print(settings.selected_model)
PY
)"; then
    fail "Runtime profile configuration is valid" \
        "Correct the profile values in .env and rerun this script."
fi
DEFAULT_PROFILE="$(printf '%s\n' "${CONFIG_SUMMARY}" | sed -n '1p')"
OLLAMA_BASE_URL_VALUE="$(printf '%s\n' "${CONFIG_SUMMARY}" | sed -n '2p')"
SELECTED_MODEL="$(printf '%s\n' "${CONFIG_SUMMARY}" | sed -n '3p')"
pass "Runtime profile configuration is valid: ${DEFAULT_PROFILE}"
pass "Default Ollama model resolved: ${SELECTED_MODEL}"

if ! REQUIRED_MODELS="$("${VENV_PYTHON}" - <<'PY'
from interview_local.config import Settings

settings = Settings.from_env()
if settings.ollama_model:
    print(f"default override\t{settings.selected_model}")
for name in settings.profiles:
    if name == "deep" and not settings.enable_deep_profile:
        continue
    print(f"{name} profile\t{settings.for_profile(name).selected_model}")
PY
)"; then
    fail "Required Ollama models resolved" \
        "Correct the Ollama model values in .env and rerun this script."
fi
pass "Required Ollama models resolved from enabled runtime profiles"

if command -v ollama >/dev/null 2>&1; then
    OLLAMA_COMMAND="$(command -v ollama)"
elif command -v ollama.exe >/dev/null 2>&1; then
    OLLAMA_COMMAND="$(command -v ollama.exe)"
else
    fail "Ollama command is available" "Install Ollama and ensure it is on PATH."
fi
pass "Ollama command is available: ${OLLAMA_COMMAND}"

OLLAMA_TAGS_URL="${OLLAMA_BASE_URL_VALUE}/api/tags"
if http_ok "${OLLAMA_TAGS_URL}"; then
    pass "Ollama service is already running: ${OLLAMA_BASE_URL_VALUE}"
elif [[ "${CHECK_ONLY}" == true ]]; then
    fail "Ollama service is already running" \
        "Start it with: ollama serve"
else
    case "${OLLAMA_BASE_URL_VALUE}" in
        http://localhost:*|http://127.0.0.1:*)
            mkdir -p "${PROJECT_ROOT}/output"
            "${OLLAMA_COMMAND}" serve >"${OLLAMA_LOG}" 2>&1 &
            OLLAMA_PID=$!
            if ! wait_for_url "${OLLAMA_TAGS_URL}"; then
                fail "Ollama service started" \
                    "Ollama did not become ready; inspect ${OLLAMA_LOG}."
            fi
            pass "Ollama service started as managed process ${OLLAMA_PID}"
            ;;
        *)
            fail "Ollama service is reachable" \
                "Start the configured service at ${OLLAMA_BASE_URL_VALUE}."
            ;;
    esac
fi

MODEL_CHECK_FAILED=false
while IFS=$'\t' read -r model_scope required_model; do
    [[ -n "${model_scope}" && -n "${required_model}" ]] || continue
    if OLLAMA_STATUS="$("${VENV_PYTHON}" - \
        "${OLLAMA_BASE_URL_VALUE}" "${required_model}" <<'PY'
import sys

from interview_local.service import check_ollama

status = check_ollama(sys.argv[1], sys.argv[2])
print(status.message)
raise SystemExit(0 if status.ok else 1)
PY
)"; then
        pass "Required Ollama model is downloaded for ${model_scope}: ${required_model}"
    else
        pending "Required Ollama model is downloaded for ${model_scope}: ${required_model}"
        printf '    %s\n' "${OLLAMA_STATUS}" >&2
        printf '    Download it with: %s pull %s\n' \
            "${OLLAMA_COMMAND}" "${required_model}" >&2
        MODEL_CHECK_FAILED=true
    fi
done <<<"${REQUIRED_MODELS}"

if [[ "${MODEL_CHECK_FAILED}" == true ]]; then
    printf '    Download every missing model, then rerun this script.\n' >&2
    exit 1
fi

LIVE_URL="http://${APP_HOST}:${APP_PORT}/api/v1/health/live"
READY_URL="http://${APP_HOST}:${APP_PORT}/api/v1/health/ready"
if http_ok "${LIVE_URL}"; then
    pass "Interview Atelier server is already running: http://${APP_HOST}:${APP_PORT}"
    if http_ok "${READY_URL}"; then
        pass "Existing Interview Atelier server is ready"
        exit 0
    fi
    fail "Existing Interview Atelier server is ready" \
        "The process responded to liveness but failed readiness."
fi

if port_open "${APP_HOST}" "${APP_PORT}"; then
    fail "Application port is available" \
        "Port ${APP_PORT} is occupied by another process."
fi
pass "Application port is available: ${APP_HOST}:${APP_PORT}"

if [[ "${CHECK_ONLY}" == true ]]; then
    pass "All checks passed; Uvicorn is ready to start"
    exit 0
fi

pass "All startup checks passed"
pass "Application will be available at http://${APP_HOST}:${APP_PORT}"
printf '\nStarting Uvicorn in the foreground; server output follows.\n'
printf 'Keep this terminal open and press Ctrl+C to stop the server.\n\n'

printf 'job_interview app here: http://localhost:8000 \n\n'

"${VENV_PYTHON}" -m uvicorn interview_local.api.app:app \
    --host "${APP_HOST}" \
    --port "${APP_PORT}"
