from fastapi.testclient import TestClient


def test_root_landing_endpoint(client: TestClient):
    """Verifies that the root landing url returns a proper status and welcoming json payload."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Welcome" in data["message"]
    assert data["status"] == "UP"


def test_liveness_probe_endpoint(client: TestClient):
    """Verifies that the /live probe returns UP, signaling that the container process is alive."""
    response = client.get("/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert "alive" in data["message"]


def test_readiness_probe_endpoint(client: TestClient):
    """Verifies that the /ready probe returns UP, signaling the application is ready to receive requests."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert "ready" in data["message"]


def test_deep_system_health_endpoint(client: TestClient):
    """Verifies that the /health endpoint executes deep checks on hardware and connections."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    # Assert top-level aggregated status fields
    assert "status" in data
    assert "system_load" in data
    assert "components" in data
    assert "version" in data
    assert "timestamp" in data
    
    # Assert hardware keys exist
    load = data["system_load"]
    assert "cpu_percent" in load
    assert "memory_percent" in load
    assert "disk_percent" in load
    
    # Assert connection endpoints statuses are registered
    comps = data["components"]
    assert "database" in comps
    assert "cache" in comps
    assert comps["database"]["status"] == "UP"
    assert comps["cache"]["status"] == "UP"
