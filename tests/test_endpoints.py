import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        # Arrange
        expected_keys = {"Chess Club", "Programming Class", "Gym Class"}
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert set(activities.keys()) >= expected_keys
        assert all("description" in v and "participants" in v for v in activities.values())
    
    def test_activity_has_required_fields(self, client, reset_activities):
        # Arrange
        # Act
        response = client.get("/activities")
        activities = response.json()
        chess_club = activities["Chess Club"]
        
        # Assert
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_valid_activity(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]
    
    def test_signup_duplicate_fails_with_400(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()
    
    def test_signup_invalid_activity_returns_404(self, client, reset_activities):
        # Arrange
        activity_name = "NonExistent Activity"
        email = "test@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_adds_participant_to_list(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response1 = client.get("/activities")
        initial_count = len(response1.json()[activity_name]["participants"])
        
        client.post(f"/activities/{activity_name}/signup", params={"email": email})
        response2 = client.get("/activities")
        
        # Assert
        final_count = len(response2.json()[activity_name]["participants"])
        assert final_count == initial_count + 1
        assert email in response2.json()[activity_name]["participants"]


class TestRemove:
    """Tests for DELETE /activities/{activity_name}/remove endpoint"""
    
    def test_remove_valid_participant(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Known participant
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/remove",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]
    
    def test_remove_nonexistent_participant_returns_404(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email = "nobody@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/remove",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_remove_invalid_activity_returns_404(self, client, reset_activities):
        # Arrange
        activity_name = "NonExistent Activity"
        email = "test@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/remove",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
    
    def test_remove_updates_participant_list(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act
        response1 = client.get("/activities")
        initial_count = len(response1.json()[activity_name]["participants"])
        
        client.delete(f"/activities/{activity_name}/remove", params={"email": email})
        response2 = client.get("/activities")
        
        # Assert
        final_count = len(response2.json()[activity_name]["participants"])
        assert final_count == initial_count - 1
        assert email not in response2.json()[activity_name]["participants"]


class TestIntegration:
    """Integration tests combining multiple operations"""
    
    def test_signup_then_remove_flow(self, client, reset_activities):
        # Arrange
        activity_name = "Programming Class"
        email = "integration_test@mergington.edu"
        
        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        get_response_after_signup = client.get("/activities")
        
        # Act - Remove
        remove_response = client.delete(
            f"/activities/{activity_name}/remove",
            params={"email": email}
        )
        get_response_after_remove = client.get("/activities")
        
        # Assert
        assert signup_response.status_code == 200
        assert email in get_response_after_signup.json()[activity_name]["participants"]
        
        assert remove_response.status_code == 200
        assert email not in get_response_after_remove.json()[activity_name]["participants"]
