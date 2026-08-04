"""Observer-independent progress events for long-running workflows."""

from __future__ import annotations

from collections.abc import Callable

ProgressCallback = Callable[[str, str, int, int], None]


def emit_progress(
    callback: ProgressCallback | None,
    stage: str,
    message: str,
    completed_steps: int,
    total_steps: int,
) -> None:
    """Emit progress without allowing observer failures to break domain work."""
    if callback is None:
        return
    try:
        callback(stage, message, completed_steps, total_steps)
    except Exception:
        return
