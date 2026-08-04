"""CrewAI LLM construction and structured-output parsing helpers."""

from __future__ import annotations

import json
from typing import Any, TypeVar

from json_repair import loads as repair_json
from pydantic import BaseModel

from interview_local.config import Settings

ModelT = TypeVar("ModelT", bound=BaseModel)


def _json_shape(schema: dict[str, Any], root: dict[str, Any]) -> Any:
    """Turn JSON Schema into a compact value-shaped example for smaller models."""
    if "$ref" in schema:
        target: Any = root
        for part in schema["$ref"].removeprefix("#/").split("/"):
            target = target[part]
        return _json_shape(target, root)
    if "anyOf" in schema:
        choice = next(
            (
                option
                for option in schema["anyOf"]
                if option.get("type") != "null"
            ),
            schema["anyOf"][0],
        )
        return _json_shape(choice, root)
    if "enum" in schema:
        return schema["enum"][0]

    schema_type = schema.get("type")
    if schema_type == "object" or "properties" in schema:
        return {
            key: _json_shape(value, root)
            for key, value in schema.get("properties", {}).items()
        }
    if schema_type == "array":
        return [_json_shape(schema.get("items", {}), root)]
    if schema_type in {"integer", "number"}:
        return schema.get("minimum", 0)
    if schema_type == "boolean":
        return False
    return ""


def schema_instruction(model_type: type[BaseModel]) -> str:
    """Describe a strict contract as a value shape that small models can follow."""
    schema = model_type.model_json_schema()
    shape = _json_shape(schema, schema)
    return (
        "\n\nOUTPUT CONTRACT\n"
        "Return exactly one JSON object and no Markdown fences or commentary. "
        "Use double-quoted JSON keys and strings, include every required field, "
        "and do not leave trailing commas. Do not output a JSON Schema: never return "
        "`$defs`, `properties`, `title`, or `type` metadata. Fill this value-shaped "
        "example with actual results. Add array items as needed and preserve the exact "
        "keys and value types:\n"
        f"{json.dumps(shape, indent=2)}"
    )


def create_llm(settings: Settings, temperature: float = 0.2) -> Any:
    """Create the configured CrewAI LLM backed by local Ollama."""
    from crewai import LLM

    arguments: dict[str, Any] = {
        "model": settings.crewai_model,
        "base_url": settings.ollama_base_url.rstrip("/"),
        "temperature": temperature,
        "timeout": settings.llm_timeout_seconds,
        "max_retries": 2,
        "max_tokens": settings.selected_max_tokens,
        "additional_params": {
            "reasoning_effort": settings.ollama_reasoning_effort
        },
    }
    # CrewAI's OpenAI-compatible Ollama adapter only forwards this setting
    # when it is placed in additional_params. Keeping hidden thinking off
    # prevents a thinking-capable model from consuming the full completion
    # budget before it emits the structured answer.
    return LLM(**arguments)


def structured_result(result: Any, model_type: type[ModelT]) -> ModelT:
    """Return a Pydantic model from CrewAI output, repairing JSON as a fallback."""
    value = getattr(result, "pydantic", None)
    if value is not None:
        return value if isinstance(value, model_type) else model_type.model_validate(value)

    raw = getattr(result, "raw", None) or str(result)
    try:
        data = repair_json(raw)
        return model_type.model_validate(data)
    except Exception as exc:
        preview = raw[:500].replace("\n", " ")
        raise ValueError(
            f"The local model did not return valid {model_type.__name__} data. "
            f"Output started with: {preview}"
        ) from exc


def structured_result_with_retry(
    result: Any,
    model_type: type[ModelT],
    retry_agent: Any,
    *,
    max_retries: int = 1,
) -> ModelT:
    """Repair locally first, then ask the same agent for one bounded correction."""
    current = result
    first_error: ValueError | None = None
    for attempt in range(max_retries + 1):
        try:
            return structured_result(current, model_type)
        except ValueError as exc:
            if first_error is None:
                first_error = exc
            if attempt >= max_retries:
                raise first_error from exc

        raw = (getattr(current, "raw", None) or str(current))[:40_000]
        correction_prompt = (
            f"Correct the following invalid {model_type.__name__} output. "
            "Preserve its supported content, fix only JSON syntax and schema violations, "
            "and do not add unsupported facts.\n\n"
            f"INVALID OUTPUT\n{raw}"
            + schema_instruction(model_type)
        )
        try:
            current = retry_agent.kickoff(correction_prompt)
        except Exception as exc:
            if "none or empty" in str(exc).lower():
                raise ValueError(
                    f"{first_error} The automatic correction call also returned no content."
                ) from exc
            raise

    raise RuntimeError("Unreachable structured-output retry state.")
