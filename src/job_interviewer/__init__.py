"""Local-first multi-agent job interview coach."""

import os

# Keep user documents and workflow metadata out of CrewAI telemetry by default. An
# operator can explicitly override this before importing the package.
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

__version__ = "0.2.3"
# Increment for fixes that do not warrant a semantic-version change. Deployments may
# override this with APP_BUILD_TAG (for example a CI run number or Git short SHA).
__build_tag__ = "20260731.3"
