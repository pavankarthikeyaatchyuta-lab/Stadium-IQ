from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_navigate_endpoint():
    payload = {
        "from_location": "gate_a",
        "to_location": "gate_b",
        "language": "English",
        "context": {
            "current_time": "19:45",
            "match_phase": "halftime"
        }
    }
    response = client.post("/navigate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "path" in data
    assert "directions" in data

def test_crowd_endpoint():
    payload = {
        "language": "English",
        "context": {
            "match_phase": "halftime"
        }
    }
    response = client.post("/crowd", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "risk_analysis" in data
    assert "choke_pressure" in data

def test_fan_endpoint():
    payload = {
        "query": "Where is the nearest food court?",
        "language": "English",
        "context": {}
    }
    response = client.post("/fan", json=payload)
    assert response.status_code == 200
    # Returns a string response directly in fan endpoint
    assert isinstance(response.json(), str)

def test_scenario_endpoint():
    payload = {
        "scenario_type": "gate_closure",
        "scenario_params": {"gate": "A"},
        "language": "English",
        "context": {}
    }
    response = client.post("/scenario", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "computed_impact" in data

def test_copilot_endpoint():
    payload = {
        "language": "English",
        "context": {}
    }
    response = client.post("/copilot", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "situation_summary" in data

def test_input_validation_422():
    # Missing required field `query` for fan endpoint
    payload = {
        "language": "English",
        "context": {}
    }
    response = client.post("/fan", json=payload)
    assert response.status_code == 422

def test_oversized_payload_validation():
    # Testing max_length constraint
    payload = {
        "query": "A" * 1000,  # Exceeds max length of 500
        "language": "English",
        "context": {}
    }
    response = client.post("/fan", json=payload)
    assert response.status_code == 422

def test_sustainability_endpoint():
    payload = {
        "language": "English",
        "context": {}
    }
    response = client.post("/sustainability", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "eco_tip" in data
