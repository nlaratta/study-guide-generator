import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app as app_module  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module.config, "RESPONSES_FILE", str(tmp_path / "saved.json"))
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


@pytest.fixture
def fake_openai(monkeypatch):
    """Replace the OpenAI client with a stub; records the calls made."""
    calls = []

    class _Completions:
        def create(self, **kwargs):
            calls.append(kwargs)
            msg = type("M", (), {"content": "# mocked answer"})()
            return type("R", (), {"choices": [type("C", (), {"message": msg})()]})()

    class _Client:
        chat = type("Chat", (), {"completions": _Completions()})()

    monkeypatch.setattr(app_module, "get_client", lambda: _Client())
    return calls
