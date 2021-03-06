# Prefect Discord

Prefect Discord is a lightweight package to send notifications from flows and tasks to a Discord channel.
The alerting system is configurable and allows many options that suit different flows and tasks.

## Usage Example
```python
from prefect import task
from prefect_discord import discord_notifier
@task(state_handlers=[discord_notifier(ignore_states=[Running])])
def add(x, y):
    return x + y
```

## Configuration

### Environment Variables
`prefect_discord` expects a few secrets set on Prefect's `config.toml`:
- `DISCORD_WEBHOOK_URL` = "discord_channel_webhook_url"
- `DISCORD_WEBHOOK_THUMBNAIL_URL` = "url_for_the_main_image"
- `DISCORD_WEBHOOK_FOOTER_MESSAGE` = "footer_text_next_to_icon"
- `DISCORD_WEBHOOK_FOOTER_ICON_URL` = "url_for_the_footer_image"

### State Handler Parameters
The state handler can also be configured with some options
- ignore_states ([State], optional): list of `State` classes to ignore, e.g.,
    `[Running, Scheduled]`. If `new_state` is an instance of one of the passed states,
    no notification will occur.
- only_states ([State], optional): similar to `ignore_states`, but instead _only_
    notifies you if the Task / Flow is in a state from the provided list of `State`
    classes
- webhook_secret (str, optional): the name of the Prefect Secret that stores your Discord
    webhook URL; defaults to `"DISCORD_WEBHOOK_URL"`
- backend_info (bool, optional): Whether to supply the Discord notification with urls
    pointing to backend pages; defaults to True
- proxies (dict), optional): `dict` with "http" and/or "https" keys, passed to
    `requests.post` - for situations where a proxy is required to send requests to the
    Discrd webhook