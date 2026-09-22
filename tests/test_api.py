import sys
from pathlib import Path


# Add the backend directory to Python's import path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_DIR))


from app import app


def test_health_endpoint():
    """
    Test whether the backend health endpoint works.
    """

    app.config["TESTING"] = True

    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200

    response_data = response.get_json()

    assert response_data["status"] == "healthy"

    assert response_data["service"] == (
        "ResQCloud Backend"
    )


def test_infrastructure_endpoint():
    """
    Test whether the infrastructure endpoint works.
    """

    app.config["TESTING"] = True

    client = app.test_client()

    response = client.get(
        "/api/v1/infrastructure"
    )

    assert response.status_code == 200

    response_data = response.get_json()

    assert response_data["status"] == (
        "operational"
    )

    assert "resources" in response_data


def test_backups_endpoint():
    """
    Test whether the backups endpoint works.
    """

    app.config["TESTING"] = True

    client = app.test_client()

    response = client.get(
        "/api/v1/backups"
    )

    assert response.status_code == 200

    response_data = response.get_json()

    assert response_data["status"] == "success"

    assert "backups" in response_data


def test_incidents_endpoint():
    """
    Test whether the incidents endpoint works.
    """

    app.config["TESTING"] = True

    client = app.test_client()

    response = client.get(
        "/api/v1/incidents"
    )

    assert response.status_code == 200

    response_data = response.get_json()

    assert response_data["status"] == "success"

    assert "incidents" in response_data


def test_recovery_requests_endpoint():
    """
    Test whether the recovery requests endpoint works.
    """

    app.config["TESTING"] = True

    client = app.test_client()

    response = client.get(
        "/api/v1/recovery-requests"
    )

    assert response.status_code == 200

    response_data = response.get_json()

    assert response_data["status"] == "success"

    assert "recovery_requests" in response_data


def test_create_backup_without_required_fields():
    """
    Test that an invalid backup request is rejected.
    """

    app.config["TESTING"] = True

    client = app.test_client()

    response = client.post(
        "/api/v1/backups",
        json={}
    )

    assert response.status_code == 400

    response_data = response.get_json()

    assert "error" in response_data


def test_create_incident_without_required_fields():
    """
    Test that an invalid incident request is rejected.
    """

    app.config["TESTING"] = True

    client = app.test_client()

    response = client.post(
        "/api/v1/incidents",
        json={}
    )

    assert response.status_code == 400

    response_data = response.get_json()

    assert "error" in response_data


def test_create_recovery_request_without_required_fields():
    """
    Test that an invalid recovery request is rejected.
    """

    app.config["TESTING"] = True

    client = app.test_client()

    response = client.post(
        "/api/v1/recovery-requests",
        json={}
    )

    assert response.status_code == 400

    response_data = response.get_json()

    assert "error" in response_data


def test_create_recovery_request_with_invalid_status():
    """
    Test that an invalid recovery status is rejected.
    """

    app.config["TESTING"] = True

    client = app.test_client()

    response = client.post(
        "/api/v1/recovery-requests",
        json={
            "resource_name": "Test Server",
            "recovery_type": "Full Recovery",
            "status": "invalid_status",
            "reason": "Testing invalid status"
        }
    )

    assert response.status_code == 400

    response_data = response.get_json()

    assert "error" in response_data