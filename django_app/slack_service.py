"""
Slack API service utility for handling interactions with Slack API.
"""
from typing import List, Dict, Optional, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackService:
    """Service class for interacting with Slack API."""

    def __init__(self, access_token: str):
        """Initialize SlackService with access token."""
        self.client = WebClient(token=access_token)
        self.access_token = access_token

    def test_auth(self) -> Dict[str, Any]:
        """Test authentication with the provided token."""
        try:
            response = self.client.auth_test()
            return {
                'success': True,
                'data': response.data
            }
        except SlackApiError as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_channels(self) -> Dict[str, Any]:
        """Get list of all channels the bot can access."""
        try:
            # Get public channels
            public_channels = self.client.conversations_list(
                types="public_channel",
                exclude_archived=True
            )

            # Get private channels
            private_channels = self.client.conversations_list(
                types="private_channel",
                exclude_archived=True
            )

            # Get DMs
            dms = self.client.conversations_list(
                types="im",
                exclude_archived=True
            )

            all_channels = []

            # Add public channels
            for channel in public_channels['channels']:
                all_channels.append({
                    'id': channel['id'],
                    'name': f"#{channel['name']}",
                    'type': 'public_channel',
                    'is_member': channel.get('is_member', False)
                })

            # Add private channels
            for channel in private_channels['channels']:
                all_channels.append({
                    'id': channel['id'],
                    'name': f"#{channel['name']}",
                    'type': 'private_channel',
                    'is_member': channel.get('is_member', False)
                })

            # Add DMs
            for dm in dms['channels']:
                user_info = self.client.users_info(user=dm['user'])
                all_channels.append({
                    'id': dm['id'],
                    'name': f"@{user_info['user']['real_name'] or user_info['user']['name']}",
                    'type': 'im',
                    'is_member': True
                })

            return {
                'success': True,
                'channels': all_channels
            }
        except SlackApiError as e:
            return {
                'success': False,
                'error': str(e)
            }

    def post_message(self, channel_id: str, text: str) -> Dict[str, Any]:
        """Post a message to a channel."""
        try:
            response = self.client.chat_postMessage(
                channel=channel_id,
                text=text
            )
            return {
                'success': True,
                'message': response.data
            }
        except SlackApiError as e:
            return {
                'success': False,
                'error': str(e)
            }

    def post_reply(self, channel_id: str, thread_ts: str, text: str) -> Dict[str, Any]:
        """Post a reply to a thread."""
        try:
            response = self.client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text=text
            )
            return {
                'success': True,
                'message': response.data
            }
        except SlackApiError as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_channel_history(self, channel_id: str, limit: int = 10) -> Dict[str, Any]:
        """Get recent messages from a channel."""
        try:
            response = self.client.conversations_history(
                channel=channel_id,
                limit=limit
            )

            messages = []
            for message in response['messages']:
                if message.get('type') == 'message' and not message.get('subtype'):
                    messages.append({
                        'ts': message['ts'],
                        'text': message['text'],
                        'user': message.get('user'),
                        'thread_ts': message.get('thread_ts'),
                        'reply_count': message.get('reply_count', 0)
                    })

            return {
                'success': True,
                'messages': messages
            }
        except SlackApiError as e:
            return {
                'success': False,
                'error': str(e)
            }