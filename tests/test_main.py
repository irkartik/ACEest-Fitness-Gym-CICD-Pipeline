import os
import tempfile
import pytest
from app.main import app as flask_app, init_db


@pytest.fixture
def client():
    """Create a test client with a temporary database."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    flask_app.config["TESTING"] = True
    os.environ["ACEEST_DB"] = db_path

    # Re-import to pick up the new DB_PATH at module level
    import app.main as main_module
    main_module.DB_PATH = db_path
    init_db()

    with flask_app.test_client() as test_client:
        yield test_client

    os.close(db_fd)
    os.unlink(db_path)


# ---------- Health ----------


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "healthy"
    assert "ACEest" in data["app"]


# ---------- Programs ----------


def test_get_programs(client):
    resp = client.get("/api/programs")
    assert resp.status_code == 200
    data = resp.get_json()
    expected = {"Fat Loss (FL)", "Muscle Gain (MG)", "Beginner (BG)"}
    assert set(data.keys()) == expected


def test_get_program_by_name(client):
    resp = client.get("/api/programs/Fat Loss (FL)")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "Fat Loss (FL)" in data


def test_get_program_not_found(client):
    resp = client.get("/api/programs/NonExistent")
    assert resp.status_code == 404


def test_get_site_metrics(client):
    resp = client.get("/api/site-metrics")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["capacity"] == 150
    assert data["area_sqft"] == 10000
    assert data["break_even_members"] == 250


# ---------- Clients CRUD ----------


def test_create_client(client):
    resp = client.post("/api/clients", json={
        "name": "Raju",
        "age": 25,
        "weight": 75,
        "height": 175,
        "program": "Fat Loss (FL)",
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["message"] == "Client 'Raju' created"
    assert data["calories"] == 75 * 22  # weight * fat loss factor


def test_create_client_missing_name(client):
    resp = client.post("/api/clients", json={"age": 25})
    assert resp.status_code == 400


def test_create_duplicate_client(client):
    client.post("/api/clients", json={"name": "Raju"})
    resp = client.post("/api/clients", json={"name": "Raju"})
    assert resp.status_code == 409


def test_list_clients(client):
    client.post("/api/clients", json={"name": "Alice"})
    client.post("/api/clients", json={"name": "Bob"})
    resp = client.get("/api/clients")
    assert resp.status_code == 200
    data = resp.get_json()
    names = [c["name"] for c in data]
    assert "Alice" in names
    assert "Bob" in names


def test_get_client(client):
    client.post("/api/clients", json={"name": "Raju", "age": 25})
    resp = client.get("/api/clients/Raju")
    assert resp.status_code == 200
    assert resp.get_json()["name"] == "Raju"
    assert resp.get_json()["age"] == 25


def test_get_client_not_found(client):
    resp = client.get("/api/clients/Ghost")
    assert resp.status_code == 404


def test_update_client(client):
    client.post("/api/clients", json={
        "name": "Raju",
        "weight": 75,
        "program": "Fat Loss (FL)",
    })
    resp = client.put("/api/clients/Raju", json={
        "weight": 80,
        "program": "Muscle Gain (MG)",
    })
    assert resp.status_code == 200

    updated = client.get("/api/clients/Raju").get_json()
    assert updated["weight"] == 80
    assert updated["program"] == "Muscle Gain (MG)"
    assert updated["calories"] == 80 * 35  # weight * muscle gain factor


def test_update_client_not_found(client):
    resp = client.put("/api/clients/Ghost", json={"weight": 80})
    assert resp.status_code == 404


def test_delete_client(client):
    client.post("/api/clients", json={"name": "Raju"})
    resp = client.delete("/api/clients/Raju")
    assert resp.status_code == 200

    resp = client.get("/api/clients/Raju")
    assert resp.status_code == 404


def test_delete_client_not_found(client):
    resp = client.delete("/api/clients/Ghost")
    assert resp.status_code == 404


# ---------- Workouts ----------


def test_log_and_list_workouts(client):
    client.post("/api/clients", json={"name": "Raju"})

    resp = client.post("/api/clients/Raju/workouts", json={
        "date": "2026-03-07",
        "workout_type": "Strength",
        "duration_min": 60,
        "notes": "Heavy squats",
    })
    assert resp.status_code == 201

    resp = client.get("/api/clients/Raju/workouts")
    assert resp.status_code == 200
    workouts = resp.get_json()
    assert len(workouts) == 1
    assert workouts[0]["workout_type"] == "Strength"
    assert workouts[0]["duration_min"] == 60


def test_log_workout_missing_date(client):
    resp = client.post("/api/clients/Raju/workouts", json={
        "workout_type": "Strength",
    })
    assert resp.status_code == 400


# ---------- Progress ----------


def test_log_and_list_progress(client):
    client.post("/api/clients", json={"name": "Raju"})

    resp = client.post("/api/clients/Raju/progress", json={
        "week": "Week 10 - 2026",
        "adherence": 85,
    })
    assert resp.status_code == 201

    resp = client.get("/api/clients/Raju/progress")
    assert resp.status_code == 200
    progress = resp.get_json()
    assert len(progress) == 1
    assert progress[0]["adherence"] == 85
    assert progress[0]["week"] == "Week 10 - 2026"


def test_log_progress_missing_fields(client):
    resp = client.post("/api/clients/Raju/progress", json={"week": "Week 1"})
    assert resp.status_code == 400

    resp = client.post("/api/clients/Raju/progress", json={"adherence": 80})
    assert resp.status_code == 400
