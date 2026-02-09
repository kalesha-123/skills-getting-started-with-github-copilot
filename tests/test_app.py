"""Tests for the FastAPI activities application"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state after each test"""
    # Store original state
    original_activities = {
        name: {
            "description": activity["description"],
            "schedule": activity["schedule"],
            "max_participants": activity["max_participants"],
            "participants": activity["participants"].copy()
        }
        for name, activity in activities.items()
    }
    
    yield
    
    # Restore original state
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, dict)
        assert "Tennis Club" in data
        assert "Basketball Team" in data
        assert "Art Studio" in data
        assert "Theater Club" in data
        assert "Debate Team" in data
        assert "Science Club" in data
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_contains_correct_structure(self, client, reset_activities):
        """Test that each activity has the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_succeeds_with_valid_activity_and_email(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Tennis%20Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Signed up newstudent@mergington.edu for Tennis Club"
        
        # Verify student was added
        assert "newstudent@mergington.edu" in activities["Tennis Club"]["participants"]
    
    def test_signup_fails_with_nonexistent_activity(self, client, reset_activities):
        """Test that signup fails for nonexistent activity"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_signup_fails_if_already_signed_up(self, client, reset_activities):
        """Test that signup fails if student is already signed up"""
        # alex@mergington.edu is already in Tennis Club
        response = client.post(
            "/activities/Tennis%20Club/signup",
            params={"email": "alex@mergington.edu"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student already signed up for this activity"
    
    def test_signup_increases_participant_count(self, client, reset_activities):
        """Test that signup increases the participant count"""
        initial_count = len(activities["Basketball Team"]["participants"])
        
        client.post(
            "/activities/Basketball%20Team/signup",
            params={"email": "newplayer@mergington.edu"}
        )
        
        final_count = len(activities["Basketball Team"]["participants"])
        assert final_count == initial_count + 1


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_succeeds_with_valid_activity_and_email(self, client, reset_activities):
        """Test successful unregister from an activity"""
        # First verify the student is signed up
        assert "alex@mergington.edu" in activities["Tennis Club"]["participants"]
        
        response = client.delete(
            "/activities/Tennis%20Club/unregister",
            params={"email": "alex@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Unregistered alex@mergington.edu from Tennis Club"
        
        # Verify student was removed
        assert "alex@mergington.edu" not in activities["Tennis Club"]["participants"]
    
    def test_unregister_fails_with_nonexistent_activity(self, client, reset_activities):
        """Test that unregister fails for nonexistent activity"""
        response = client.delete(
            "/activities/Nonexistent%20Activity/unregister",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_unregister_fails_if_not_signed_up(self, client, reset_activities):
        """Test that unregister fails if student is not signed up"""
        response = client.delete(
            "/activities/Tennis%20Club/unregister",
            params={"email": "notstudent@mergington.edu"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student is not signed up for this activity"
    
    def test_unregister_decreases_participant_count(self, client, reset_activities):
        """Test that unregister decreases the participant count"""
        # james@mergington.edu is in Basketball Team
        initial_count = len(activities["Basketball Team"]["participants"])
        
        client.delete(
            "/activities/Basketball%20Team/unregister",
            params={"email": "james@mergington.edu"}
        )
        
        final_count = len(activities["Basketball Team"]["participants"])
        assert final_count == initial_count - 1


class TestIntegration:
    """Integration tests for signup and unregister flows"""
    
    def test_signup_then_unregister_flow(self, client, reset_activities):
        """Test the complete flow of signing up and then unregistering"""
        email = "integrationtest@mergington.edu"
        activity = "Tennis Club"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        assert email in activities[activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        assert email not in activities[activity]["participants"]
    
    def test_multiple_signups_and_unregisters(self, client, reset_activities):
        """Test multiple students signing up and unregistering"""
        activity = "Art Studio"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        # Sign up multiple students
        for email in emails:
            response = client.post(
                "/activities/Art%20Studio/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all are signed up
        for email in emails:
            assert email in activities[activity]["participants"]
        
        # Unregister all
        for email in emails:
            response = client.delete(
                "/activities/Art%20Studio/unregister",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all are unregistered
        for email in emails:
            assert email not in activities[activity]["participants"]
