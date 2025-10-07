Slack Console is a demo app that demostrates usage of the Slack API

# Dependencies

- django
- Tailwind CSS

# User stories

- enter an access token in the UI
- choose a channel to post to from the list of all channels
- post a message to the selected channel
  - recently posted messages are displayed in the "Recent activiy" section
- post a reply in a thread for a message in "Recent activity"

# Non-functional requirements

- assume that the bot is not added to any channels, so APIs like conversations.history won't work