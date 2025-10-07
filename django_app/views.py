import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone

from .models import SlackToken, SlackMessage
from .slack_service import SlackService


class HomeView(View):
    """Main home view for the Slack Console."""

    def get(self, request):
        # Get stored tokens for the dropdown
        tokens = SlackToken.objects.filter(is_active=True)

        # Get recent messages
        recent_messages = SlackMessage.objects.all()[:20]

        context = {
            'tokens': tokens,
            'recent_messages': recent_messages,
        }
        return render(request, 'django_app/home.html', context)


class TokenView(View):
    """View for managing Slack tokens."""

    def post(self, request):
        token = request.POST.get('token', '').strip()
        name = request.POST.get('name', '').strip()

        if not token:
            messages.error(request, 'Please provide a valid Slack token.')
            return redirect('home')

        if not name:
            name = f"Token {SlackToken.objects.count() + 1}"

        # Test the token
        slack_service = SlackService(token)
        auth_result = slack_service.test_auth()

        if not auth_result['success']:
            messages.error(request, f"Invalid token: {auth_result['error']}")
            return redirect('home')

        # Save the token
        team_name = auth_result['data'].get('team', '')
        user_name = auth_result['data'].get('user', '')

        slack_token = SlackToken.objects.create(
            name=name,
            token=token,
            team_name=team_name,
            user_name=user_name
        )

        messages.success(request, f'Token added successfully for team: {team_name}')

        # Store token ID in session for easy access
        request.session['current_token_id'] = slack_token.id

        return redirect('home')


class ChannelsView(View):
    """View for getting channels list via AJAX."""

    def get(self, request):
        token_id = request.GET.get('token_id')

        if not token_id:
            return JsonResponse({'success': False, 'error': 'No token selected'})

        try:
            token = SlackToken.objects.get(id=token_id, is_active=True)
        except SlackToken.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid token'})

        # Update last used
        token.last_used = timezone.now()
        token.save()

        slack_service = SlackService(token.token)
        channels_result = slack_service.get_channels()

        return JsonResponse(channels_result)


class PostMessageView(View):
    """View for posting messages to Slack channels."""

    def post(self, request):
        token_id = request.POST.get('token_id')
        channel_id = request.POST.get('channel_id')
        channel_name = request.POST.get('channel_name')
        message_text = request.POST.get('message_text', '').strip()

        if not all([token_id, channel_id, message_text]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('home')

        try:
            token = SlackToken.objects.get(id=token_id, is_active=True)
        except SlackToken.DoesNotExist:
            messages.error(request, 'Invalid token selected.')
            return redirect('home')

        slack_service = SlackService(token.token)
        result = slack_service.post_message(channel_id, message_text)

        if result['success']:
            # Store the message in database
            message_data = result['message']
            SlackMessage.objects.create(
                channel_id=channel_id,
                channel_name=channel_name or f"Channel {channel_id}",
                message_ts=message_data['ts'],
                text=message_text,
                user_id=message_data.get('user', 'bot'),
            )
            messages.success(request, 'Message posted successfully!')
        else:
            messages.error(request, f'Failed to post message: {result["error"]}')

        return redirect('home')



