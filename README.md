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