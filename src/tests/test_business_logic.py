"""
Unit tests for business logic using the AAA (Arrange-Act-Assert) pattern.
Tests validate core logic for email validation, participant limits, and data integrity.
"""

import pytest


class TestEmailValidation:
    """Tests for email validation logic."""

    def test_valid_email_format_accepted(self, client):
        """
        Arrange: Prepare a valid email
        Act: Attempt signup with valid email
        Assert: Email is accepted (assuming it doesn't conflict)
        """
        # Arrange
        activity_name = "Chess Club"
        valid_email = "valid.student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": valid_email}
        )

        # Assert
        # Valid email format should be accepted
        assert response.status_code == 200

    def test_email_with_special_characters_accepted(self, client):
        """
        Arrange: Prepare email with special characters
        Act: Attempt signup
        Assert: Email with valid special chars is accepted
        """
        # Arrange
        activity_name = "Chess Club"
        email_with_plus = "student+tag@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email_with_plus}
        )

        # Assert
        assert response.status_code == 200
        assert email_with_plus in response.json()["message"]


class TestParticipantLimits:
    """Tests for participant limit enforcement."""

    def test_add_within_max_capacity(self, client, sample_activities):
        """
        Arrange: Identify activity with available slots
        Act: Add student when below max capacity
        Assert: Signup succeeds
        """
        # Arrange
        activity_name = "Math Club"
        current_count = len(sample_activities[activity_name]["participants"])
        max_participants = sample_activities[activity_name]["max_participants"]
        new_email = "mathstudent@mergington.edu"

        assert current_count < max_participants  # Verify has space

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )

        # Assert
        assert response.status_code == 200
        assert len(sample_activities[activity_name]["participants"]) == current_count + 1

    def test_current_count_less_than_max(self, client, sample_activities):
        """
        Arrange: Get activity with available capacity
        Act: Check participant count
        Assert: Verify count is valid
        """
        # Arrange
        activity_name = "Programming Class"

        # Act
        current_participants = sample_activities[activity_name]["participants"]
        max_capacity = sample_activities[activity_name]["max_participants"]

        # Assert
        assert len(current_participants) <= max_capacity
        assert max_capacity > 0


class TestDataIntegrity:
    """Tests for data integrity during add/remove operations."""

    def test_add_participant_updates_correct_activity(self, client, sample_activities):
        """
        Arrange: Set up two activities
        Act: Add participant to one activity
        Assert: Verify only target activity is updated
        """
        # Arrange
        activity_1 = "Chess Club"
        activity_2 = "Drama Club"
        email = "uniquestudent@mergington.edu"
        count_1_before = len(sample_activities[activity_1]["participants"])
        count_2_before = len(sample_activities[activity_2]["participants"])

        # Act
        response = client.post(
            f"/activities/{activity_1}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert len(sample_activities[activity_1]["participants"]) == count_1_before + 1
        assert len(sample_activities[activity_2]["participants"]) == count_2_before

    def test_remove_participant_updates_correct_activity(self, client, sample_activities):
        """
        Arrange: Set up two activities with participants
        Act: Remove participant from one activity
        Assert: Verify only target activity is updated
        """
        # Arrange
        activity_1 = "Chess Club"
        activity_2 = "Programming Class"
        email_to_remove = "michael@mergington.edu"
        email_to_keep = "emma@mergington.edu"

        count_1_before = len(sample_activities[activity_1]["participants"])
        count_2_before = len(sample_activities[activity_2]["participants"])

        # Act
        response = client.delete(
            f"/activities/{activity_1}/unregister",
            params={"email": email_to_remove}
        )

        # Assert
        assert response.status_code == 200
        assert len(sample_activities[activity_1]["participants"]) == count_1_before - 1
        assert len(sample_activities[activity_2]["participants"]) == count_2_before

    def test_no_duplicate_participants_after_signup(self, client, sample_activities):
        """
        Arrange: Add a participant
        Act: Verify participant appears exactly once
        Assert: No duplicates in participants list
        """
        # Arrange
        activity_name = "Science Club"
        email = "science@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        participants = sample_activities[activity_name]["participants"]
        count_of_email = participants.count(email)
        assert count_of_email == 1

    def test_remove_correct_participant_only(self, client, sample_activities):
        """
        Arrange: Activity with multiple participants
        Act: Remove one specific participant
        Assert: Verify only that participant removed, others untouched
        """
        # Arrange
        activity_name = "Tennis Club"
        email_to_remove = "rachel@mergington.edu"
        other_emails = [
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
        remaining = sample_activities[activity_name]["participants"]
        assert email_to_remove not in remaining
        for other_email in other_emails:
            assert other_email in remaining
