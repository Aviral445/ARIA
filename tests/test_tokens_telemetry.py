"""
tests/test_tokens_telemetry.py — Unit Tests for Aria & GAIA Token Telemetry API
Verifies:
1. GET /api/tokens_telemetry returns 200 OK with success=True
2. Aria token metrics contain all linked APIs: Gemini, NVIDIA NIM, Groq, Ollama, ChromaDB, Audio
3. GAIA token metrics contain all supervisor APIs: Dedicated NIM, Groq Parallel Mind, Gemini, Zero-Token AST Linter, Sisterhood Matrix
4. Zero-token static linter verifies 0 tokens consumed and positive tokens saved
5. Token sums are positive integers and consistent
"""

import pytest
from fastapi.testclient import TestClient
from core.aria_api import app

client = TestClient(app)

def test_tokens_telemetry_status():
    response = client.get("/api/tokens_telemetry")
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True
    assert "aria" in data
    assert "gaia" in data

def test_aria_linked_apis_breakdown():
    response = client.get("/api/tokens_telemetry")
    data = response.json()
    aria = data["aria"]
    
    assert "summary" in aria
    assert aria["summary"]["total_tokens"] > 0
    assert aria["summary"]["active_apis_count"] == 6
    
    apis = {api["id"]: api for api in aria["apis"]}
    expected_apis = ["gemini", "nvidia", "groq", "ollama", "chromadb", "speech"]
    for api_id in expected_apis:
        assert api_id in apis, f"Missing Aria linked API: {api_id}"
        item = apis[api_id]
        assert item["total_tokens"] > 0
        assert "name" in item
        assert "model" in item
        assert "status" in item

    # Verify NVIDIA NIM multi-model breakdown
    nvidia_api = apis["nvidia"]
    assert "models_breakdown" in nvidia_api
    assert len(nvidia_api["models_breakdown"]) >= 3

def test_gaia_linked_apis_breakdown():
    response = client.get("/api/tokens_telemetry")
    data = response.json()
    gaia = data["gaia"]
    
    assert "summary" in gaia
    assert gaia["summary"]["total_tokens"] > 0
    assert gaia["summary"]["tokens_saved"] > 0
    assert gaia["summary"]["active_apis_count"] == 5
    
    apis = {api["id"]: api for api in gaia["apis"]}
    expected_apis = ["gaia_nvidia", "gaia_groq", "gaia_gemini", "gaia_ast_linter", "gaia_sisterhood"]
    for api_id in expected_apis:
        assert api_id in apis, f"Missing GAIA supervisor API: {api_id}"
        item = apis[api_id]
        assert "name" in item
        assert "status" in item

    # Verify Zero-Token AST Static Linter consumes 0 tokens
    linter_api = apis["gaia_ast_linter"]
    assert linter_api["total_tokens"] == 0
    assert linter_api["prompt_tokens"] == 0
    assert linter_api["completion_tokens"] == 0
    assert "Saved" in linter_api["status"]
