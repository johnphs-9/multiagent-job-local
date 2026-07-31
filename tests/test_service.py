import io
import json
from urllib.error import URLError

from job_interviewer.service import check_ollama


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def test_check_ollama_finds_model(monkeypatch) -> None:
    payload = json.dumps({"models": [{"name": "gemma4:latest"}]}).encode()
    monkeypatch.setattr(
        "job_interviewer.service.urlopen",
        lambda *args, **kwargs: FakeResponse(payload),
    )

    status = check_ollama("http://localhost:11434", "gemma4:latest")

    assert status.ok
    assert "gemma4:latest" in status.message


def test_check_ollama_reports_missing_model(monkeypatch) -> None:
    payload = json.dumps({"models": [{"name": "llama3.2:latest"}]}).encode()
    monkeypatch.setattr(
        "job_interviewer.service.urlopen",
        lambda *args, **kwargs: FakeResponse(payload),
    )

    status = check_ollama("http://localhost:11434", "gemma4:latest")

    assert not status.ok
    assert "llama3.2:latest" in status.message


def test_check_ollama_reports_connection_failure(monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise URLError("offline")

    monkeypatch.setattr("job_interviewer.service.urlopen", fail)

    status = check_ollama("http://localhost:11434", "gemma4:latest")

    assert not status.ok
    assert "ollama serve" in status.message

