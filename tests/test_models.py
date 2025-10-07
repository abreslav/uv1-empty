"""
Unit tests for django_app models.
"""
import pytest
from django.test import TestCase
from django.utils import timezone
from django_app.models import SlackMessage, SlackToken


class SlackMessageTestCase(TestCase):
    """Test cases for SlackMessage model."""

    def setUp(self):
        """Set up test data."""
        self.parent_message = SlackMessage.objects.create(
            channel_id="C123456789",
            channel_name="general",
            message_ts="1234567890.123456",
            text="This is a parent message",
            user_id="U123456789"
        )

        self.reply_message = SlackMessage.objects.create(
            channel_id="C123456789",
            channel_name="general",
            message_ts="1234567891.123456",
            text="This is a reply",
            thread_ts="1234567890.123456",
            user_id="U987654321"
        )

    @pytest.mark.timeout(30)
    def test_slack_message_str(self):
        """Test kind: unit_tests - SlackMessage.__str__"""
        expected = "Message in general: This is a parent message..."
        self.assertEqual(str(self.parent_message), expected)

        # Test with long text that gets truncated
        long_message = SlackMessage.objects.create(
            channel_id="C123456789",
            channel_name="general",
            message_ts="1234567892.123456",
            text="This is a very long message that should be truncated at 50 characters and show ellipsis",
            user_id="U123456789"
        )
        expected_long = "Message in general: This is a very long message that should be truncat..."
        self.assertEqual(str(long_message), expected_long)



class SlackTokenTestCase(TestCase):
    """Test cases for SlackToken model."""

    def setUp(self):
        """Set up test data."""
        self.token = SlackToken.objects.create(
            name="Test Token",
            token="xoxb-test-token",
            team_name="Test Team",
            user_name="testuser"
        )

        self.token_no_team = SlackToken.objects.create(
            name="Token No Team",
            token="xoxb-another-token",
            team_name="",
            user_name="anotheruser"
        )

    @pytest.mark.timeout(30)
    def test_slack_token_str(self):
        """Test kind: unit_tests - SlackToken.__str__"""
        expected = "Test Token - Test Team"
        self.assertEqual(str(self.token), expected)

        # Test with empty team name
        expected_no_team = "Token No Team - "
        self.assertEqual(str(self.token_no_team), expected_no_team)