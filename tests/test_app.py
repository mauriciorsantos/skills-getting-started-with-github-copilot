"""
Backend tests for the Mergington High School Activities API
Using the AAA (Arrange-Act-Assert) testing pattern
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to known state before each test"""
    # Arrange: Initialize activities with clean state
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu"]
        }
    })
    yield


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


class TestGetActivities:
    """Tests for retrieving activities"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all available activities"""
        # Arrange: test client is ready
        # Act: fetch all activities
        response = client.get("/activities")
        
        # Assert: response is successful and contains expected data
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert data["Chess Club"]["max_participants"] == 12


class TestSignup:
    """Tests for student signup functionality"""

    def test_signup_adds_participant_to_activity(self, client):
        """Test that a student can successfully sign up for an activity"""
        # Arrange: known activity and student email
        activity_name = "Chess Club"
        email = "alice@mergington.edu"
        
        # Act: send signup request
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert: signup succeeds and participant is added
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        assert email in activities[activity_name]["participants"]

    def test_signup_normalizes_email(self, client):
        """Test that emails are normalized to lowercase"""
        # Arrange: uppercase email
        activity_name = "Chess Club"
        email = "ALICE@MERGINGTON.EDU"
        
        # Act: send signup with uppercase email
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert: email is normalized to lowercase in participants
        assert response.status_code == 200
        assert "alice@mergington.edu" in activities[activity_name]["participants"]

    def test_signup_prevents_duplicate_registration(self, client):
        """Test that a student cannot sign up twice for the same activity"""
        # Arrange: student already in participants
        activity_name = "Chess Club"
        email = "alice@mergington.edu"
        # First signup
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Act: attempt duplicate signup
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert: duplicate signup is rejected
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
        # Verify participant appears only once
        assert activities[activity_name]["participants"].count("alice@mergington.edu") == 1

    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test that signing up for a non-existent activity returns 404"""
        # Arrange: invalid activity name
        activity_name = "Nonexistent Club"
        email = "alice@mergington.edu"
        
        # Act: attempt signup for invalid activity
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert: 404 error is returned
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestRemoveParticipant:
    """Tests for removing participants from activities"""

    def test_remove_participant_succeeds(self, client):
        """Test that a participant can be successfully removed from an activity"""
        # Arrange: participant is in the activity
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        
        # Act: remove participant
        response = client.delete(
            f"/activities/{activity_name}/participants?email={email}"
        )
        
        # Assert: participant is removed
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]
        assert email not in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count - 1

    def test_remove_participant_not_found(self, client):
        """Test that removing a non-existent participant returns 404"""
        # Arrange: participant is not in the activity
        activity_name = "Chess Club"
        email = "nobody@mergington.edu"
        
        # Act: attempt to remove non-existent participant
        response = client.delete(
            f"/activities/{activity_name}/participants?email={email}"
        )
        
        # Assert: 404 error is returned
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_remove_participant_from_nonexistent_activity(self, client):
        """Test that removing from a non-existent activity returns 404"""
        # Arrange: invalid activity
        activity_name = "Nonexistent Club"
        email = "someone@mergington.edu"
        
        # Act: attempt removal from invalid activity
        response = client.delete(
            f"/activities/{activity_name}/participants?email={email}"
        )
        
        # Assert: 404 error is returned
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestIntegration:
    """Integration tests combining multiple operations"""

    def test_signup_and_remove_flow(self, client):
        """Test complete flow: signup, verify, then remove"""
        # Arrange: activity and email ready
        activity_name = "Programming Class"
        email = "bob@mergington.edu"
        
        # Act & Assert: signup
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        assert email in activities[activity_name]["participants"]
        
        # Act & Assert: remove
        remove_response = client.delete(
            f"/activities/{activity_name}/participants?email={email}"
        )
        assert remove_response.status_code == 200
        assert email not in activities[activity_name]["participants"]
