"""
Comprehensive test suite for the Mergington High School Activities API.

Tests cover both endpoints with full coverage including:
- Happy path scenarios (successful requests)
- Error cases (invalid inputs, duplicates, not found)
- Edge cases and validation scenarios
"""

import pytest


class TestGetActivities:
    """Tests for the GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all 9 activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        assert "Basketball Team" in data
        assert "Swimming Club" in data
        assert "Art Club" in data
        assert "Drama Society" in data
        assert "Math Olympiad" in data
        assert "Science Club" in data

    def test_get_activities_response_structure(self, client):
        """Test that each activity has required fields."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        for activity_name, activity_data in data.items():
            # Each activity must have these fields
            assert "description" in activity_data, f"{activity_name} missing description"
            assert "schedule" in activity_data, f"{activity_name} missing schedule"
            assert "max_participants" in activity_data, f"{activity_name} missing max_participants"
            assert "participants" in activity_data, f"{activity_name} missing participants"
            
            # Verify field types
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_initial_participants(self, client):
        """Test that activities have expected initial participants."""
        response = client.get("/activities")
        data = response.json()
        
        # Chess Club should have 2 initial participants
        assert len(data["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]
        
        # Programming Class should have 2 initial participants
        assert len(data["Programming Class"]["participants"]) == 2
        assert "emma@mergington.edu" in data["Programming Class"]["participants"]

    def test_get_activities_participants_is_list(self, client):
        """Test that participants field is always a list."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["participants"], list), \
                f"{activity_name} participants should be a list"


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""

    def test_signup_successful(self, client):
        """Test successful signup with valid activity name and email."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds the participant to the activity."""
        # Get initial state
        response_before = client.get("/activities")
        data_before = response_before.json()
        initial_count = len(data_before["Chess Club"]["participants"])
        
        # Perform signup
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        
        # Verify participant was added
        response_after = client.get("/activities")
        data_after = response_after.json()
        assert len(data_after["Chess Club"]["participants"]) == initial_count + 1
        assert "newstudent@mergington.edu" in data_after["Chess Club"]["participants"]

    def test_signup_multiple_students_same_activity(self, client):
        """Test that multiple different students can signup for the same activity."""
        # Sign up first student
        response1 = client.post(
            "/activities/Programming Class/signup",
            params={"email": "alice@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Sign up second student
        response2 = client.post(
            "/activities/Programming Class/signup",
            params={"email": "bob@mergington.edu"}
        )
        assert response2.status_code == 200
        
        # Verify both are in the activity
        response = client.get("/activities")
        data = response.json()
        participants = data["Programming Class"]["participants"]
        assert "alice@mergington.edu" in participants
        assert "bob@mergington.edu" in participants

    def test_signup_duplicate_email_returns_400(self, client):
        """Test that signup with duplicate email returns 400 Bad Request."""
        # michael@mergington.edu is already in Chess Club
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Already registered" in data["detail"]

    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test that signup for non-existent activity returns 404 Not Found."""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_signup_case_sensitive_activity_name(self, client):
        """Test that activity names are case-sensitive."""
        # "chess club" (lowercase) should not match "Chess Club"
        response = client.post(
            "/activities/chess club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404

    def test_signup_with_special_characters_in_email(self, client):
        """Test that signup accepts emails with special characters."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "student.name+tag@mergington.edu"}
        )
        assert response.status_code == 200
        
        # Verify it was added to participants
        response_get = client.get("/activities")
        data = response_get.json()
        assert "student.name+tag@mergington.edu" in data["Chess Club"]["participants"]

    def test_signup_with_different_domains(self, client):
        """Test that signup accepts emails with different domains."""
        # The API doesn't validate email format, so any string should work
        response = client.post(
            "/activities/Art Club/signup",
            params={"email": "user@example.com"}
        )
        assert response.status_code == 200

    def test_signup_empty_email_string(self, client):
        """Test signup with empty email string."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": ""}
        )
        # Empty string is still a valid parameter, should be accepted
        assert response.status_code == 200

    def test_signup_persists_across_requests(self, client):
        """Test that data persists across multiple requests (integration test)."""
        # Signup student 1
        client.post(
            "/activities/Swimming Club/signup",
            params={"email": "student1@mergington.edu"}
        )
        
        # Signup student 2
        client.post(
            "/activities/Swimming Club/signup",
            params={"email": "student2@mergington.edu"}
        )
        
        # Get activities and verify both are present
        response = client.get("/activities")
        data = response.json()
        participants = data["Swimming Club"]["participants"]
        assert "student1@mergington.edu" in participants
        assert "student2@mergington.edu" in participants
        # Original participants should still be there
        assert "liam@mergington.edu" in participants
        assert "ava@mergington.edu" in participants

    def test_signup_to_multiple_activities(self, client):
        """Test that a student can sign up for multiple different activities."""
        # Sign up same student to different activities
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": "versatile@mergington.edu"}
        )
        assert response1.status_code == 200
        
        response2 = client.post(
            "/activities/Art Club/signup",
            params={"email": "versatile@mergington.edu"}
        )
        assert response2.status_code == 200
        
        # Verify student is in both activities
        response = client.get("/activities")
        data = response.json()
        assert "versatile@mergington.edu" in data["Chess Club"]["participants"]
        assert "versatile@mergington.edu" in data["Art Club"]["participants"]

    def test_signup_response_format(self, client):
        """Test that signup response has correct format."""
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Response should be a dict with a "message" key
        assert isinstance(data, dict)
        assert "message" in data
        assert isinstance(data["message"], str)

    def test_signup_duplicate_across_different_activities(self, client):
        """Test that same email can signup for multiple activities."""
        response1 = client.post(
            "/activities/Drama Society/signup",
            params={"email": "multitasker@mergington.edu"}
        )
        response2 = client.post(
            "/activities/Music Club/signup",
            params={"email": "multitasker@mergington.edu"}
        )
        
        # Second response should be 404 because "Music Club" doesn't exist
        # This test verifies the scoping is per activity
        assert response1.status_code == 200
        assert response2.status_code == 404  # Music Club doesn't exist


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_activity_max_participants_not_enforced(self, client):
        """
        Edge case: max_participants field exists but is not enforced.
        
        Document current behavior: students can signup even if activity is at capacity.
        This test verifies the current implementation detail.
        """
        # Chess Club has max_participants: 12
        # Sign up many students to exceed this
        for i in range(15):
            response = client.post(
                "/activities/Chess Club/signup",
                params={"email": f"student{i}@mergington.edu"}
            )
            # Should succeed even beyond max_participants
            assert response.status_code == 200
        
        # Verify all were added
        response = client.get("/activities")
        data = response.json()
        assert len(data["Chess Club"]["participants"]) == 2 + 15  # 2 initial + 15 new

    def test_whitespace_in_email(self, client):
        """Test signup with whitespace in email (edge case)."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "  student@mergington.edu  "}
        )
        # Whitespace is preserved (API doesn't trim)
        assert response.status_code == 200

    def test_all_activities_accessible_via_signup(self, client):
        """Test that all 9 activities can be accessed via signup endpoint."""
        activities_list = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Swimming Club",
            "Art Club",
            "Drama Society",
            "Math Olympiad",
            "Science Club"
        ]
        
        for activity_name in activities_list:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": f"test_{activity_name}@mergington.edu"}
            )
            assert response.status_code == 200, f"Failed to signup for {activity_name}"

    def test_unicode_characters_in_email(self, client):
        """Test signup with unicode characters (edge case)."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "étudiant@mergington.edu"}
        )
        # Should accept unicode in email parameter
        assert response.status_code == 200

    def test_very_long_email(self, client):
        """Test signup with very long email address."""
        long_email = "a" * 200 + "@mergington.edu"
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": long_email}
        )
        # Should accept long emails
        assert response.status_code == 200


class TestIntegration:
    """Integration tests combining multiple endpoints and scenarios."""

    def test_full_workflow_signup_and_retrieve(self, client):
        """Test full workflow: signup and retrieve updated activities."""
        # Step 1: Get initial state
        response1 = client.get("/activities")
        initial_chess_count = len(response1.json()["Chess Club"]["participants"])
        
        # Step 2: Signup new student
        signup_response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "workflow@mergington.edu"}
        )
        assert signup_response.status_code == 200
        
        # Step 3: Get updated state
        response2 = client.get("/activities")
        final_chess_count = len(response2.json()["Chess Club"]["participants"])
        
        # Verify the change
        assert final_chess_count == initial_chess_count + 1
        assert "workflow@mergington.edu" in response2.json()["Chess Club"]["participants"]

    def test_multiple_activities_independent(self, client):
        """Test that changes to one activity don't affect others."""
        # Get initial counts
        response1 = client.get("/activities")
        chess_initial = len(response1.json()["Chess Club"]["participants"])
        art_initial = len(response1.json()["Art Club"]["participants"])
        
        # Signup to Chess Club only
        client.post(
            "/activities/Chess Club/signup",
            params={"email": "chess_only@mergington.edu"}
        )
        
        # Get updated state
        response2 = client.get("/activities")
        chess_final = len(response2.json()["Chess Club"]["participants"])
        art_final = len(response2.json()["Art Club"]["participants"])
        
        # Art Club should be unchanged
        assert art_final == art_initial
        # Chess Club should have one more
        assert chess_final == chess_initial + 1

    def test_error_doesnt_modify_state(self, client):
        """Test that failed requests don't modify the activity state."""
        # Get initial Chess Club participants
        response1 = client.get("/activities")
        initial_participants = response1.json()["Chess Club"]["participants"].copy()
        
        # Try to signup with duplicate email (should fail)
        client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}  # Already registered
        )
        
        # Get final state
        response2 = client.get("/activities")
        final_participants = response2.json()["Chess Club"]["participants"]
        
        # Participants should be unchanged
        assert final_participants == initial_participants
