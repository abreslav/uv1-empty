"""
Endpoint tests for django_app views.
"""
import pytest
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.utils import timezone
from unittest.mock import patch, MagicMock
from django_app.models import SlackToken, SlackMessage


class HomeViewTestCase(TestCase):
    """Test cases for HomeView endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.token = SlackToken.objects.create(
            name="Test Token",
            token="xoxb-test-token",
            team_name="Test Team",
            user_name="testuser"
        )
        self.message = SlackMessage.objects.create(
            channel_id="C123456789",
            channel_name="general",
            message_ts="1234567890.123456",
            text="Test message",
            user_id="U123456789"
        )

    @pytest.mark.timeout(30)
    def test_home_view_get(self):
        """Test kind: endpoint_tests - HomeView.get"""
        response = self.client.get('/')

        # Should return successful response
        self.assertEqual(response.status_code, 200)

        # Should contain expected context data
        self.assertIn('tokens', response.context)
        self.assertIn('recent_messages', response.context)

        # Should contain our test data
        tokens = response.context['tokens']
        self.assertEqual(tokens.count(), 1)
        self.assertEqual(tokens.first(), self.token)

        recent_messages = response.context['recent_messages']
        self.assertIn(self.message, recent_messages)


class TokenViewTestCase(TestCase):
    """Test cases for TokenView endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()

    @pytest.mark.timeout(30)
    @patch('django_app.views.SlackService')
    def test_token_view_post_success(self, mock_slack_service_class):
        """Test kind: endpoint_tests - TokenView.post"""
        # Mock successful auth test
        mock_slack_service = MagicMock()
        mock_slack_service.test_auth.return_value = {
            'success': True,
            'data': {
                'team': 'Test Team',
                'user': 'testuser'
            }
        }
        mock_slack_service_class.return_value = mock_slack_service

        response = self.client.post('/token/', {
            'token': 'xoxb-test-token',
            'name': 'Test Token'
        })

        # Should redirect to home
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

        # Should create token in database
        token = SlackToken.objects.get(token='xoxb-test-token')
        self.assertEqual(token.name, 'Test Token')
        self.assertEqual(token.team_name, 'Test Team')
        self.assertEqual(token.user_name, 'testuser')

        # Should set session variable
        self.assertEqual(self.client.session.get('current_token_id'), token.id)

    @pytest.mark.timeout(30)
    @patch('django_app.views.SlackService')
    def test_token_view_post_invalid_token(self, mock_slack_service_class):
        """Test kind: endpoint_tests - TokenView.post with invalid token"""
        # Mock failed auth test
        mock_slack_service = MagicMock()
        mock_slack_service.test_auth.return_value = {
            'success': False,
            'error': 'invalid_auth'
        }
        mock_slack_service_class.return_value = mock_slack_service

        response = self.client.post('/token/', {
            'token': 'invalid-token',
            'name': 'Test Token'
        })

        # Should redirect to home
        self.assertEqual(response.status_code, 302)

        # Should not create token
        self.assertEqual(SlackToken.objects.count(), 0)

    @pytest.mark.timeout(30)
    def test_token_view_post_empty_token(self):
        """Test kind: endpoint_tests - TokenView.post with empty token"""
        response = self.client.post('/token/', {
            'token': '',
            'name': 'Test Token'
        })

        # Should redirect to home
        self.assertEqual(response.status_code, 302)

        # Should not create token
        self.assertEqual(SlackToken.objects.count(), 0)

    @pytest.mark.timeout(30)
    @patch('django_app.views.SlackService')
    def test_token_view_post_no_name_provided(self, mock_slack_service_class):
        """Test kind: endpoint_tests - TokenView.post without name to cover line 43"""
        # Mock successful auth test
        mock_slack_service = MagicMock()
        mock_slack_service.test_auth.return_value = {
            'success': True,
            'data': {
                'team': 'Test Team',
                'user': 'testuser'
            }
        }
        mock_slack_service_class.return_value = mock_slack_service

        response = self.client.post('/token/', {
            'token': 'xoxb-test-token',
            'name': ''  # Empty name should trigger default name generation
        })

        # Should redirect to home
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

        # Should create token with default name
        token = SlackToken.objects.get(token='xoxb-test-token')
        self.assertEqual(token.name, 'Token 1')  # Default name based on count


class ChannelsViewTestCase(TestCase):
    """Test cases for ChannelsView endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.token = SlackToken.objects.create(
            name="Test Token",
            token="xoxb-test-token",
            team_name="Test Team",
            user_name="testuser"
        )

    @pytest.mark.timeout(30)
    @patch('django_app.views.SlackService')
    def test_channels_view_get_success(self, mock_slack_service_class):
        """Test kind: endpoint_tests - ChannelsView.get"""
        # Mock successful channels response
        mock_slack_service = MagicMock()
        mock_slack_service.get_channels.return_value = {
            'success': True,
            'channels': [
                {
                    'id': 'C123456789',
                    'name': '#general',
                    'type': 'public_channel',
                    'is_member': True
                }
            ]
        }
        mock_slack_service_class.return_value = mock_slack_service

        response = self.client.get('/channels/', {
            'token_id': self.token.id
        })

        # Should return successful JSON response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('channels', data)

        # Should update token's last_used field
        self.token.refresh_from_db()
        self.assertIsNotNone(self.token.last_used)

    @pytest.mark.timeout(30)
    def test_channels_view_get_no_token_id(self):
        """Test kind: endpoint_tests - ChannelsView.get without token_id"""
        response = self.client.get('/channels/')

        # Should return error response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'No token selected')

    @pytest.mark.timeout(30)
    def test_channels_view_get_invalid_token(self):
        """Test kind: endpoint_tests - ChannelsView.get with invalid token_id"""
        response = self.client.get('/channels/', {
            'token_id': 99999
        })

        # Should return error response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Invalid token')


class MessagesViewTestCase(TestCase):
    """Test cases for MessagesView endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.token = SlackToken.objects.create(
            name="Test Token",
            token="xoxb-test-token",
            team_name="Test Team",
            user_name="testuser"
        )


    @pytest.mark.timeout(30)
    def test_messages_view_get_missing_params(self):
        """Test kind: endpoint_tests - MessagesView.get with missing parameters"""
        response = self.client.get('/messages/', {
            'token_id': self.token.id
            # Missing channel_id
        })

        # Should return error response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Missing parameters')

    @pytest.mark.timeout(30)
    def test_messages_view_get_invalid_token(self):
        """Test kind: endpoint_tests - MessagesView.get with invalid token"""
        response = self.client.get('/messages/', {
            'token_id': 99999,
            'channel_id': 'C123456789'
        })

        # Should return error response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Invalid token')


class PostMessageViewTestCase(TestCase):
    """Test cases for PostMessageView endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.token = SlackToken.objects.create(
            name="Test Token",
            token="xoxb-test-token",
            team_name="Test Team",
            user_name="testuser"
        )

    @pytest.mark.timeout(30)
    @patch('django_app.views.SlackService')
    def test_post_message_view_post_success(self, mock_slack_service_class):
        """Test kind: endpoint_tests - PostMessageView.post"""
        # Mock successful message post
        mock_slack_service = MagicMock()
        mock_slack_service.post_message.return_value = {
            'success': True,
            'message': {
                'ts': '1234567890.123456',
                'channel': 'C123456789',
                'user': 'U999999999'
            }
        }
        mock_slack_service_class.return_value = mock_slack_service

        response = self.client.post('/post-message/', {
            'token_id': self.token.id,
            'channel_id': 'C123456789',
            'channel_name': 'general',
            'message_text': 'Test message'
        })

        # Should redirect to home
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

        # Should create message in database
        message = SlackMessage.objects.get(message_ts='1234567890.123456')
        self.assertEqual(message.channel_id, 'C123456789')
        self.assertEqual(message.channel_name, 'general')
        self.assertEqual(message.text, 'Test message')
        self.assertEqual(message.user_id, 'U999999999')

    @pytest.mark.timeout(30)
    @patch('django_app.views.SlackService')
    def test_post_message_view_post_failure(self, mock_slack_service_class):
        """Test kind: endpoint_tests - PostMessageView.post with API failure"""
        # Mock failed message post
        mock_slack_service = MagicMock()
        mock_slack_service.post_message.return_value = {
            'success': False,
            'error': 'channel_not_found'
        }
        mock_slack_service_class.return_value = mock_slack_service

        response = self.client.post('/post-message/', {
            'token_id': self.token.id,
            'channel_id': 'C123456789',
            'channel_name': 'general',
            'message_text': 'Test message'
        })

        # Should redirect to home
        self.assertEqual(response.status_code, 302)

        # Should not create message in database
        self.assertEqual(SlackMessage.objects.count(), 0)

    @pytest.mark.timeout(30)
    def test_post_message_view_post_missing_fields(self):
        """Test kind: endpoint_tests - PostMessageView.post with missing fields"""
        response = self.client.post('/post-message/', {
            'token_id': self.token.id,
            'channel_id': 'C123456789'
            # Missing message_text and channel_name
        })

        # Should redirect to home
        self.assertEqual(response.status_code, 302)

        # Should not create message
        self.assertEqual(SlackMessage.objects.count(), 0)

    @pytest.mark.timeout(30)
    def test_post_message_view_post_invalid_token_id(self):
        """Test kind: endpoint_tests - PostMessageView.post with invalid token_id to cover lines 111-113"""
        response = self.client.post('/post-message/', {
            'token_id': 99999,  # Non-existent token ID
            'channel_id': 'C123456789',
            'channel_name': 'general',
            'message_text': 'Test message'
        })

        # Should redirect to home
        self.assertEqual(response.status_code, 302)

        # Should not create message
        self.assertEqual(SlackMessage.objects.count(), 0)


class PostReplyViewTestCase(TestCase):
    """Test cases for PostReplyView endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.token = SlackToken.objects.create(
            name="Test Token",
            token="xoxb-test-token",
            team_name="Test Team",
            user_name="testuser"
        )


    @pytest.mark.timeout(30)
    @patch('django_app.views.SlackService')
    def test_post_reply_view_post_failure(self, mock_slack_service_class):
        """Test kind: endpoint_tests - PostReplyView.post with API failure"""
        # Mock failed reply post
        mock_slack_service = MagicMock()
        mock_slack_service.post_reply.return_value = {
            'success': False,
            'error': 'thread_not_found'
        }
        mock_slack_service_class.return_value = mock_slack_service

        response = self.client.post('/post-reply/', {
            'token_id': self.token.id,
            'channel_id': 'C123456789',
            'channel_name': 'general',
            'thread_ts': '1234567890.123456',
            'reply_text': 'Test reply'
        })

        # Should redirect to home
        self.assertEqual(response.status_code, 302)

        # Should not create reply in database
        self.assertEqual(SlackMessage.objects.count(), 0)

    @pytest.mark.timeout(30)
    def test_post_reply_view_post_missing_fields(self):
        """Test kind: endpoint_tests - PostReplyView.post with missing fields"""
        response = self.client.post('/post-reply/', {
            'token_id': self.token.id,
            'channel_id': 'C123456789'
            # Missing thread_ts, reply_text, and channel_name
        })

        # Should redirect to home
        self.assertEqual(response.status_code, 302)

        # Should not create reply
        self.assertEqual(SlackMessage.objects.count(), 0)

    @pytest.mark.timeout(30)
    def test_post_reply_view_post_invalid_token(self):
        """Test kind: endpoint_tests - PostReplyView.post with invalid token"""
        response = self.client.post('/post-reply/', {
            'token_id': 99999,
            'channel_id': 'C123456789',
            'channel_name': 'general',
            'thread_ts': '1234567890.123456',
            'reply_text': 'Test reply'
        })

        # Should redirect to home
        self.assertEqual(response.status_code, 302)

        # Should not create reply
        self.assertEqual(SlackMessage.objects.count(), 0)