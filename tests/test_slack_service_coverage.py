"""
Coverage tests for slack_service to ensure all code paths are tested.
These complement the external API tests with mock-based tests to achieve full coverage.
"""
import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from slack_sdk.errors import SlackApiError
from django_app.slack_service import SlackService


class SlackServiceCoverageTestCase(TestCase):
    """Coverage-focused tests for SlackService to supplement external API tests."""

    def setUp(self):
        """Set up test data."""
        self.slack_service = SlackService("xoxb-test-token")

    @pytest.mark.timeout(30)
    @patch('django_app.slack_service.WebClient')
    def test_slack_service_test_auth_success_path(self, mock_web_client_class):
        """Test kind: external_api_tests - SlackService.test_auth success path coverage"""
        # Mock successful response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = {
            'ok': True,
            'url': 'https://test.slack.com/',
            'team': 'Test Team',
            'user': 'testuser',
            'team_id': 'T123456',
            'user_id': 'U123456'
        }
        mock_client.auth_test.return_value = mock_response
        mock_web_client_class.return_value = mock_client

        service = SlackService("valid-token")
        result = service.test_auth()

        # Should cover line 21 (success path return)
        self.assertTrue(result['success'])
        self.assertIn('data', result)
        self.assertEqual(result['data'], mock_response.data)

    @pytest.mark.timeout(30)
    @patch('django_app.slack_service.WebClient')
    def test_slack_service_get_channels_success_path(self, mock_web_client_class):
        """Test kind: external_api_tests - SlackService.get_channels success path coverage"""
        # Mock successful responses for all channel types
        mock_client = MagicMock()

        # Mock public channels
        mock_client.conversations_list.side_effect = [
            {  # Public channels call
                'channels': [
                    {
                        'id': 'C123456',
                        'name': 'general',
                        'is_member': True
                    }
                ]
            },
            {  # Private channels call
                'channels': [
                    {
                        'id': 'C789012',
                        'name': 'private',
                        'is_member': False
                    }
                ]
            },
            {  # DMs call
                'channels': [
                    {
                        'id': 'D345678',
                        'user': 'U123456'
                    }
                ]
            }
        ]

        # Mock user info for DMs
        mock_client.users_info.return_value = {
            'user': {
                'name': 'testuser',
                'real_name': 'Test User'
            }
        }

        mock_web_client_class.return_value = mock_client

        service = SlackService("valid-token")
        result = service.get_channels()

        # Should cover all success paths including lines 41, 47, 52, 55-56, 64-65, 73-75, 82
        self.assertTrue(result['success'])
        self.assertIn('channels', result)
        channels = result['channels']
        self.assertEqual(len(channels), 3)

        # Check public channel formatting
        public_channel = channels[0]
        self.assertEqual(public_channel['name'], '#general')
        self.assertEqual(public_channel['type'], 'public_channel')

        # Check private channel formatting
        private_channel = channels[1]
        self.assertEqual(private_channel['name'], '#private')
        self.assertEqual(private_channel['type'], 'private_channel')

        # Check DM formatting
        dm_channel = channels[2]
        self.assertEqual(dm_channel['name'], '@Test User')
        self.assertEqual(dm_channel['type'], 'im')

    @pytest.mark.timeout(30)
    @patch('django_app.slack_service.WebClient')
    def test_slack_service_post_message_success_path(self, mock_web_client_class):
        """Test kind: external_api_tests - SlackService.post_message success path coverage"""
        # Mock successful response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = {
            'ok': True,
            'ts': '1234567890.123456',
            'channel': 'C123456',
            'message': {
                'text': 'Test message'
            }
        }
        mock_client.chat_postMessage.return_value = mock_response
        mock_web_client_class.return_value = mock_client

        service = SlackService("valid-token")
        result = service.post_message("C123456", "Test message")

        # Should cover line 99 (success path return)
        self.assertTrue(result['success'])
        self.assertIn('message', result)
        self.assertEqual(result['message'], mock_response.data)


