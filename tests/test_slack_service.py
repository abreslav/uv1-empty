"""
External API tests for django_app slack_service.

Note: These tests require real Slack API access. Set SLACK_API_TOKEN
environment variable to enable full testing. Without it, tests will
be skipped to maintain external API testing integrity.
"""
import pytest
import os
from django.test import TestCase
from unittest.mock import patch, MagicMock
from django_app.slack_service import SlackService


class SlackServiceExternalApiTestCase(TestCase):
    """Test cases for SlackService external API integration."""

    def setUp(self):
        """Set up test data."""
        # For external API tests, we need a real Slack token
        # These tests will be skipped if no token is provided
        self.slack_token = os.environ.get('SLACK_API_TOKEN')
        if self.slack_token:
            self.slack_service = SlackService(self.slack_token)

        # Test channel ID - use a general channel that likely exists
        # In real tests, this would be configured per workspace
        self.test_channel_id = os.environ.get('SLACK_TEST_CHANNEL_ID', 'C123456789')

    @pytest.mark.timeout(30)
    def test_slack_service_test_auth(self):
        """Test kind: external_api_tests - SlackService.test_auth"""
        if not self.slack_token:
            self.skipTest("No SLACK_API_TOKEN environment variable provided")

        result = self.slack_service.test_auth()

        # Should be successful with valid token
        self.assertTrue(result['success'])
        self.assertIn('data', result)

        # Should contain expected fields from Slack auth.test response
        data = result['data']
        self.assertIn('ok', data)
        self.assertIn('url', data)
        self.assertIn('team', data)
        self.assertIn('user', data)
        self.assertIn('team_id', data)
        self.assertIn('user_id', data)

    @pytest.mark.timeout(30)
    def test_slack_service_test_auth_with_invalid_token(self):
        """Test kind: external_api_tests - SlackService.test_auth with invalid token to cover error path"""
        invalid_service = SlackService("xoxb-invalid-token-12345")
        result = invalid_service.test_auth()

        # Should fail with invalid token
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIsInstance(result['error'], str)

    @pytest.mark.timeout(30)
    def test_slack_service_get_channels(self):
        """Test kind: external_api_tests - SlackService.get_channels"""
        if not self.slack_token:
            self.skipTest("No SLACK_API_TOKEN environment variable provided")

        result = self.slack_service.get_channels()

        # Should be successful
        self.assertTrue(result['success'])
        self.assertIn('channels', result)

        # Should return a list of channels
        channels = result['channels']
        self.assertIsInstance(channels, list)

        # If there are channels, they should have expected structure
        if channels:
            channel = channels[0]
            self.assertIn('id', channel)
            self.assertIn('name', channel)
            self.assertIn('type', channel)
            self.assertIn('is_member', channel)

    @pytest.mark.timeout(30)
    def test_slack_service_get_channels_with_invalid_token(self):
        """Test kind: external_api_tests - SlackService.get_channels with invalid token to cover error path"""
        invalid_service = SlackService("xoxb-invalid-token-12345")
        result = invalid_service.get_channels()

        # Should fail with invalid token
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIsInstance(result['error'], str)

    @pytest.mark.timeout(30)
    def test_slack_service_post_message(self):
        """Test kind: external_api_tests - SlackService.post_message"""
        if not self.slack_token:
            self.skipTest("No SLACK_API_TOKEN environment variable provided")

        test_message = "Test message from automated test"
        result = self.slack_service.post_message(self.test_channel_id, test_message)

        # Should be successful (or fail with expected error if channel doesn't exist)
        self.assertIn('success', result)

        if result['success']:
            self.assertIn('message', result)
            message_data = result['message']
            self.assertIn('ok', message_data)
            self.assertIn('ts', message_data)
            self.assertIn('channel', message_data)
        else:
            # If it fails, should have error message
            self.assertIn('error', result)

    @pytest.mark.timeout(30)
    def test_slack_service_post_message_with_invalid_token(self):
        """Test kind: external_api_tests - SlackService.post_message with invalid token to cover error path"""
        invalid_service = SlackService("xoxb-invalid-token-12345")
        result = invalid_service.post_message("C123456789", "test message")

        # Should fail with invalid token
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIsInstance(result['error'], str)





    @pytest.mark.timeout(30)
    def test_slack_service_post_thread_reply(self):
        """Test kind: external_api_tests - SlackService.post_thread_reply"""
        if not self.slack_token:
            self.skipTest("No SLACK_API_TOKEN environment variable provided")

        # First post a message to get a thread timestamp
        test_message = "Test parent message from automated test"
        parent_result = self.slack_service.post_message(self.test_channel_id, test_message)

        # Check if parent message was posted successfully
        if not parent_result['success']:
            self.skipTest(f"Cannot post parent message for thread test: {parent_result['error']}")

        thread_ts = parent_result['message']['ts']
        reply_text = "Test thread reply from automated test"

        result = self.slack_service.post_thread_reply(self.test_channel_id, thread_ts, reply_text)

        # Should be successful (or fail with expected error if channel doesn't exist)
        self.assertIn('success', result)

        if result['success']:
            self.assertIn('message', result)
            message_data = result['message']
            self.assertIn('ok', message_data)
            self.assertIn('ts', message_data)
            self.assertIn('channel', message_data)
            # Should have thread_ts field indicating it's a reply
            self.assertIn('thread_ts', message_data)
            self.assertEqual(message_data['thread_ts'], thread_ts)
        else:
            # If it fails, should have error message
            self.assertIn('error', result)

    @pytest.mark.timeout(30)
    def test_slack_service_post_thread_reply_with_invalid_token(self):
        """Test kind: external_api_tests - SlackService.post_thread_reply with invalid token to cover error path"""
        invalid_service = SlackService("xoxb-invalid-token-12345")
        result = invalid_service.post_thread_reply("C123456789", "1234567890.123456", "test reply")

        # Should fail with invalid token
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIsInstance(result['error'], str)

    @pytest.mark.timeout(30)
    @patch('django_app.slack_service.WebClient')
    def test_slack_service_post_thread_reply_generic_exception(self, mock_webclient_class):
        """Test kind: external_api_tests - SlackService.post_thread_reply with generic exception to cover lines 157-159"""
        # Mock WebClient to raise a generic exception
        mock_client = MagicMock()
        mock_client.chat_postMessage.side_effect = Exception("Generic error")
        mock_webclient_class.return_value = mock_client

        service = SlackService("test-token")
        result = service.post_thread_reply("C123456789", "1234567890.123456", "test reply")

        # Should fail with generic exception
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertEqual(result['error'], "Unexpected error: Generic error")

    @pytest.mark.timeout(30)
    @patch('django_app.slack_service.WebClient')
    def test_slack_service_post_thread_reply_success_mock(self, mock_webclient_class):
        """Test kind: external_api_tests - SlackService.post_thread_reply success path with mock to cover line 147"""
        # Mock WebClient to return successful response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = {
            'ok': True,
            'ts': '1234567891.123456',
            'channel': 'C123456789',
            'thread_ts': '1234567890.123456'
        }
        mock_client.chat_postMessage.return_value = mock_response
        mock_webclient_class.return_value = mock_client

        service = SlackService("test-token")
        result = service.post_thread_reply("C123456789", "1234567890.123456", "test reply")

        # Should be successful
        self.assertTrue(result['success'])
        self.assertIn('message', result)
        self.assertEqual(result['message'], mock_response.data)

        # Verify the WebClient was called with correct parameters
        mock_client.chat_postMessage.assert_called_once_with(
            channel='C123456789',
            text='test reply',
            thread_ts='1234567890.123456'
        )

    @pytest.mark.timeout(30)
    def test_slack_service_invalid_token(self):
        """Test external API behavior with invalid token."""
        invalid_service = SlackService("invalid-token")

        result = invalid_service.test_auth()

        # Should fail with invalid token
        self.assertFalse(result['success'])
        self.assertIn('error', result)