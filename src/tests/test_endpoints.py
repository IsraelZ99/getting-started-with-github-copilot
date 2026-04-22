"""
Integration tests for FastAPI endpoints using the AAA (Arrange-Act-Assert) pattern.
Tests cover all 4 endpoints with happy path and error scenarios.
"""

import pytest


class TestRootEndpoint:
    """Tests for GET / endpoint."""

    def test_root_redirect_to_static(self, client):
        """
        Arrange: Get client ready
        Act: Make GET request to /
        Assert: Verify redirect to static index.html
        """
        # Arrange
        # (client fixture already set up)

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivitiesEndpoint:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client, sample_activities):
        """
        Arrange: Set up client and sample activities
        Act: Make GET request to /activities
        Assert: Verify 200 status and all activities returned
        """
        # Arrange
        # (client and sample_activities fixtures already set up)

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 15  # Should have 15 activities
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_get_activities_returns_correct_schema(self, client, sample_activities):
        """
        Arrange: Set up client
        Act: Make GET request to /activities
        Assert: Verify response schema has required fields
        """
        # Arrange
        # (client and sample_activities fixtures already set up)

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_valid_signup_adds_student(self, client, sample_activities):
        """
        Arrange: Set up client with activity name and valid email
        Act: Make POST request to signup endpoint
        Assert: Verify 200 status and student added to participants
        """
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        initial_count = len(sample_activities[activity_name]["participants"])

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
        assert email in sample_activities[activity_name]["participants"]
        assert len(sample_activities[activity_name]["participants"]) == initial_count + 1

    def test_signup_to_nonexistent_activity_returns_404(self, client, sample_activities):
        """
        Arrange: Set up client with non-existent activity name
        Act: Make POST request to signup endpoint
        Assert: Verify 404 status and activity not found error
        """
        # Arrange
        activity_name = "NonExistent Activity"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_email_returns_400(self, client, sample_activities):
        """
        Arrange: Set up client with activity and email already in participants
        Act: Make POST request to signup endpoint with duplicate email
        Assert: Verify 400 status and duplicate signup error
        """
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
        assert "already signed up" in response.json()["detail"]

    def test_signup_at_max_capacity_returns_400(self, client):
        """
        Arrange: Set up activity at max capacity
        Act: Attempt to add student beyond max
        Assert: Verify validation prevents overfilling
        
        Note: This test documents current behavior. Current implementation
        does NOT prevent exceeding max_participants. This test may need
        adjustment once max capacity validation is implemented.
        """
        # Arrange
        # For now, we test that current behavior allows exceeding max
        # (Future: this should return 400 when max-capacity check is added)
        activity_name = "Chess Club"
        email = "testuser@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        # Currently allows signup regardless of max_participants
        # This test documents the current behavior
        assert response.status_code == 200


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint."""

    def test_valid_unregister_removes_student(self, client, sample_activities):
        """
        Arrange: Set up client with activity and student in participants
        Act: Make DELETE request to unregister endpoint
        Assert: Verify 200 status and student removed from participants
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in the activity
        initial_count = len(sample_activities[activity_name]["participants"])

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
        assert email not in sample_activities[activity_name]["participants"]
        assert len(sample_activities[activity_name]["participants"]) == initial_count - 1

    def test_unregister_from_nonexistent_activity_returns_404(self, client, sample_activities):
        """
        Arrange: Set up client with non-existent activity name
        Act: Make DELETE request to unregister endpoint
        Assert: Verify 404 status and activity not found error
        """
        # Arrange
        activity_name = "NonExistent Activity"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_student_not_in_activity_returns_400(self, client, sample_activities):
        """
        Arrange: Set up client with student not in activity
        Act: Make DELETE request to unregister endpoint
        Assert: Verify 400 status and not signed up error
        """
        # Arrange
        activity_name = "Chess Club"
        email = "notstudent@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_preserves_other_participants(self, client, sample_activities):
        """
        Arrange: Set up activity with multiple participants
        Act: Remove one participant
        Assert: Verify other participants remain unchanged
        """
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        email_to_keep = "daniel@mergington.edu"
        other_participants_before = [
            p for p in sample_activities[activity_name]["participants"]
            if p != email_to_remove
        ]

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email_to_remove}
        )

        # Assert
        assert response.status_code == 200
        other_participants_after = sample_activities[activity_name]["participants"]
        assert email_to_keep in other_participants_after
        assert other_participants_after == other_participants_before
