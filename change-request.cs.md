The bot is not added to any channels, so I'm getting

```
Error: The request to the Slack API failed. (url: https://slack.com/api/conversations.history) The server responded with: {'ok': False, 'error': 'not_in_channel'}
```

Remove all functionality that depends on conversations.history
