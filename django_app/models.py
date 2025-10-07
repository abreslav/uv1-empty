from django.db import models
from django.utils import timezone


class SlackMessage(models.Model):
    """Model to store Slack messages that have been sent."""

    channel_id = models.CharField(max_length=20, help_text="Slack channel ID")
    channel_name = models.CharField(max_length=100, help_text="Slack channel name")
    message_ts = models.CharField(max_length=20, unique=True, help_text="Slack message timestamp")
    text = models.TextField(help_text="Message text content")
    user_id = models.CharField(max_length=20, help_text="User ID who sent the message")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['channel_id']),
        ]

    def __str__(self):
        return f"Message in {self.channel_name}: {self.text[:50]}..."


class SlackToken(models.Model):
    """Model to store Slack access tokens (for demo purposes)."""

    name = models.CharField(max_length=100, help_text="Name/description for this token")
    token = models.CharField(max_length=200, help_text="Slack access token")
    team_name = models.CharField(max_length=100, blank=True, help_text="Team name from auth test")
    user_name = models.CharField(max_length=100, blank=True, help_text="User name from auth test")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    last_used = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.team_name}"
