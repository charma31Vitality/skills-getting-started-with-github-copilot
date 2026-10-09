from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


ACTIVITY_NAME = "Chess Club"
ACTIVITY_PATH = quote(ACTIVITY_NAME, safe="")
EMAIL = "student@example.edu"
TEST_ACTIVITIES = {
    ACTIVITY_NAME: {
        "description": "Practice strategic thinking",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": [EMAIL],
    },
    "Art Club": {
        "description": "Explore visual arts",
        "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
        "max_participants": 20,
        "participants": [],
    },
}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(TEST_ACTIVITIES))
    return TestClient(app_module.app)


def test_root_redirects_to_frontend(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_data(client):
    # Arrange
    expected_activities = deepcopy(TEST_ACTIVITIES)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant(client):
    # Arrange
    new_email = "new-student@example.edu"
    url = f"/activities/{ACTIVITY_PATH}/signup"

    # Act
    response = client.post(url, params={"email": new_email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {new_email} for {ACTIVITY_NAME}"
    }
    assert new_email in client.get("/activities").json()[ACTIVITY_NAME]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    url = f"/activities/{ACTIVITY_PATH}/signup"

    # Act
    response = client.post(url, params={"email": EMAIL})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert client.get("/activities").json()[ACTIVITY_NAME]["participants"].count(EMAIL) == 1


def test_signup_rejects_unknown_activity(client):
    # Arrange
    url = "/activities/Unknown%20Club/signup"

    # Act
    response = client.post(url, params={"email": EMAIL})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    # Arrange
    url = f"/activities/{ACTIVITY_PATH}/signup"

    # Act
    response = client.delete(url, params={"email": EMAIL})

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {EMAIL} from {ACTIVITY_NAME}"
    }
    assert EMAIL not in client.get("/activities").json()[ACTIVITY_NAME]["participants"]


def test_unregister_rejects_unregistered_participant(client):
    # Arrange
    url = f"/activities/{ACTIVITY_PATH}/signup"
    unregistered_email = "not-signed-up@example.edu"

    # Act
    response = client.delete(url, params={"email": unregistered_email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    url = "/activities/Unknown%20Club/signup"

    # Act
    response = client.delete(url, params={"email": EMAIL})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
