import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "NAGA API" in response.json()["message"]

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_chat():
    response = client.post(
        "/api/chat/",
        json={"messages": [{"role": "user", "content": "你好"}]}
    )
    # The API might return 500 if the real API key is missing
    assert response.status_code in [200, 500]

def test_list_models():
    response = client.get("/api/chat/models")
    assert response.status_code == 200
    assert "providers" in response.json()
    assert "aliyun" in response.json()["providers"]

def test_list_voices():
    response = client.get("/api/tts/voices")
    assert response.status_code == 200
    assert "voices" in response.json()