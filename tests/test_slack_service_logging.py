"""
Tests for SlackService logging functionality.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from slack_sdk.errors import SlackApiError
from django_app.slack_service import SlackService


class SlackServiceLoggingTestCase(unittest.TestCase):
    """Test cases for SlackService logging."""

    def setUp(self):
        """Set up test data."""
        self.slack_service = SlackService("test-token")

    @patch('django_app.slack_service.logger')
    def test_test_auth_logs_slack_api_error(self, mock_logger):
        """Test that SlackApiError in test_auth is properly logged."""
        # Mock the Slack client to raise a SlackApiError
        mock_response = Mock()
        slack_error = SlackApiError("The request to the Slack API failed. (url: https://slack.com/api/auth.test)", mock_response)

        with patch.object(self.slack_service.client, 'auth_test', side_effect=slack_error):
            result = self.slack_service.test_auth()

        # Verify the error was logged
        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args[0][0]
        self.assertIn("Slack API error during auth test", log_call)

        # Verify the method still returns proper error format
        self.assertFalse(result['success'])
        self.assertIn('error', result)

    @patch('django_app.slack_service.logger')
    def test_get_channels_logs_slack_api_error(self, mock_logger):
        """Test that SlackApiError in get_channels is properly logged."""
        # Mock the Slack client to raise a SlackApiError
        mock_response = Mock()
        slack_error = SlackApiError("The request to the Slack API failed. (url: https://slack.com/api/conversations.list)", mock_response)

        with patch.object(self.slack_service.client, 'conversations_list', side_effect=slack_error):
            result = self.slack_service.get_channels()

        # Verify the error was logged
        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args[0][0]
        self.assertIn("Slack API error during get_channels", log_call)

        # Verify the method still returns proper error format
        self.assertFalse(result['success'])
        self.assertIn('error', result)

    @patch('django_app.slack_service.logger')
    def test_post_message_logs_slack_api_error(self, mock_logger):
        """Test that SlackApiError in post_message is properly logged."""
        # Mock the Slack client to raise a SlackApiError
        mock_response = Mock()
        slack_error = SlackApiError("The request to the Slack API failed. (url: https://slack.com/api/chat.postMessage)", mock_response)

        channel_id = "C123456789"

        with patch.object(self.slack_service.client, 'chat_postMessage', side_effect=slack_error):
            result = self.slack_service.post_message(channel_id, "test message")

        # Verify the error was logged with channel context
        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args[0][0]
        self.assertIn(f"Slack API error during post_message to channel {channel_id}", log_call)

        # Verify the method still returns proper error format
        self.assertFalse(result['success'])
        self.assertIn('error', result)



    @patch('django_app.slack_service.logger')
    def test_test_auth_logs_unexpected_error(self, mock_logger):
        """Test that unexpected errors in test_auth are properly logged."""
        # Mock the Slack client to raise a generic exception
        with patch.object(self.slack_service.client, 'auth_test', side_effect=ValueError("Connection error")):
            result = self.slack_service.test_auth()

        # Verify the error was logged
        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args[0][0]
        self.assertIn("Unexpected error during auth test", log_call)
        self.assertIn("Connection error", log_call)

        # Verify the method still returns proper error format
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn("Unexpected error", result['error'])

    @patch('django_app.slack_service.logger')
    def test_get_channels_logs_user_info_warning(self, mock_logger):
        """Test that SlackApiError in users_info call is properly logged as warning."""
        # Mock successful conversations_list calls but failing users_info
        mock_public_channels = {'channels': []}
        mock_private_channels = {'channels': []}
        mock_dms = {'channels': [{'id': 'D123456789', 'user': 'U987654321'}]}

        # Mock the conversations_list calls to succeed
        side_effects = [mock_public_channels, mock_private_channels, mock_dms]

        # Mock users_info to fail
        mock_response = Mock()
        slack_error = SlackApiError("The request to the Slack API failed. (url: https://slack.com/api/users.info)", mock_response)

        with patch.object(self.slack_service.client, 'conversations_list', side_effect=side_effects):
            with patch.object(self.slack_service.client, 'users_info', side_effect=slack_error):
                result = self.slack_service.get_channels()

        # Verify the warning was logged for user info failure
        mock_logger.warning.assert_called_once()
        log_call = mock_logger.warning.call_args[0][0]
        self.assertIn("Failed to get user info for user U987654321", log_call)

        # Verify the method still returns success (channels list shouldn't fail due to one user lookup)
        self.assertTrue(result['success'])
        self.assertIn('channels', result)

        # Verify the channel was still added with a fallback name
        channels = result['channels']
        self.assertEqual(len(channels), 1)
        self.assertEqual(channels[0]['name'], "@user_U987654321")


if __name__ == '__main__':
    unittest.main()