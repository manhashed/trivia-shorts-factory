import pytest
import io
import json
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["ffmpeg_installed"] is True

def test_voices_endpoint():
    response = client.get("/api/voices")
    assert response.status_code == 200
    data = response.json()
    assert "edge" in data
    assert len(data["edge"]) > 0
    # Check that kid-friendly Ana voice is listed
    ana_voice = next((v for v in data["edge"] if v["id"] == "en-US-AnaNeural"), None)
    assert ana_voice is not None

def test_validate_endpoint():
    sample_json = json.dumps([
        {"q": "What color is grass?", "a": "Green"},
        {"q": "What is 2 + 2?", "a": "4"}
    ])
    files = {"file": ("trivia.json", io.BytesIO(sample_json.encode("utf-8")), "application/json")}
    response = client.post("/api/validate", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["valid_count"] == 2
    assert data["error_count"] == 0
    assert data["is_valid"] is True
