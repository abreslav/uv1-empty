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

    @pytest.mark.timeout(30)
    def test_slack_message_is_thread_reply(self):
        """Test kind: unit_tests - SlackMessage.is_thread_reply"""
        # Parent message should not be a thread reply
        self.assertFalse(self.parent_message.is_thread_reply)

        # Reply message should be a thread reply
        self.assertTrue(self.reply_message.is_thread_reply)

    @pytest.mark.timeout(30)
    def test_slack_message_get_replies(self):
        """Test kind: unit_tests - SlackMessage.get_replies"""
        # Parent message should return its replies
        replies = self.parent_message.get_replies()
        self.assertEqual(replies.count(), 1)
        self.assertEqual(replies.first(), self.reply_message)

        # Reply message should return no replies (empty queryset)
        reply_replies = self.reply_message.get_replies()
        self.assertEqual(reply_replies.count(), 0)

        # Create another reply to test multiple replies
        second_reply = SlackMessage.objects.create(
            channel_id="C123456789",
            channel_name="general",
            message_ts="1234567893.123456",
            text="This is another reply",
            thread_ts="1234567890.123456",
            user_id="U555555555"
        )

        replies = self.parent_message.get_replies()
        self.assertEqual(replies.count(), 2)
        self.assertIn(self.reply_message, replies)
        self.assertIn(second_reply, replies)


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