import app as app_module

PAYLOAD = {
    "subject": "Rust",
    "currentLevel": "beginner",
    "timeAvailable": "5",
    "learningStyle": "visual",
    "goal": "build a CLI",
    "step": 0,
    "previousResponses": [],
}


def test_home_ok(client):
    assert client.get("/").status_code == 200


def test_generate(client, fake_openai):
    r = client.post("/generate", json=PAYLOAD)
    assert r.status_code == 200
    assert r.get_json()["response"] == "# mocked answer"
    assert len(fake_openai) == 1
    assert fake_openai[0]["model"] == app_module.config.MODEL


def test_generate_uses_saved_response(client, fake_openai):
    client.post("/generate", json=PAYLOAD)
    r = client.post("/generate", json=PAYLOAD)
    assert r.get_json()["response"] == "# mocked answer"
    assert len(fake_openai) == 1  # second call served from cache


def test_component_details(client, fake_openai):
    r = client.post("/get_component_details", json={"component": "ownership", "subject": "Rust"})
    assert r.status_code == 200
    assert r.get_json()["response"] == "# mocked answer"


def test_component_details_missing_params(client):
    r = client.post("/get_component_details", json={"subject": "Rust"})
    assert r.status_code == 400


def test_missing_api_key(client, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    for path, body in (("/generate", PAYLOAD),
                       ("/get_component_details", {"component": "x", "subject": "Rust"})):
        r = client.post(path, json=body)
        assert r.status_code == 503
        assert "OPENAI_API_KEY" in r.get_json()["error"]
