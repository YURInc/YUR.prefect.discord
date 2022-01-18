# __init__.py
import requests
import datetime

from prefect import context
from prefect.client import Client, Secret
from prefect.engine.state import State
from typing import Union, cast
from prefect import Flow, Task 

from toolz import curry

def build_discord_embed(element_name: str, 
                        element_type: str,
                        new_state_name: str, 
                        state_message: str = "", 
                        thumbnail_url: str = None,
                        footer_message: str = 'Prefect Alerts',
                        footer_icon_url: str = None,
                        color = 3447003,
                        url: str = None):

    timestamp = datetime.datetime.now().isoformat()

    embed = {
        "title": "Prefect Status Update",
        "color": color,
        "timestamp": timestamp,
        "fields": [
            {
                "name": f":gear: {element_type}",
                "value": element_name
            },
            {
                "name": ":twisted_rightwards_arrows: New Status",
                "value": new_state_name
            },
            {
                "name": ":bell: Update",
                "value": state_message
            },
        ]
    }

    if footer_icon_url or footer_message:
        embed["footer"] = {
            "icon_url": footer_icon_url,
            "text": footer_message
        }

    if thumbnail_url:
        embed["thumbnail"] = {
            "url": thumbnail_url
        }

    if url: 
        embed["url"] = url

    return embed

def discord_message_formatter(
    tracked_obj: Union["Flow", "Task"],
    state: State,
    backend_info: bool = True,
) -> dict:
    element_type = None
    if isinstance(tracked_obj, Flow):
        element_type = 'Flow'
    elif isinstance(tracked_obj, Task):
        element_type = 'Task'

    url = None
    if backend_info and context.get("flow_run_id"):

        if isinstance(tracked_obj, Flow):
            url = Client().get_cloud_url(
                "flow-run", context["flow_run_id"], as_user=False
            )
        elif isinstance(tracked_obj, Task):
            url = Client().get_cloud_url(
                "task-run", context.get("task_run_id", ""), as_user=False
            )

    embed = build_discord_embed(
        element_name=tracked_obj.name,
        element_type=element_type,
        new_state_name=type(state).__name__,
        state_message=state.message,
        thumbnail_url=Secret("DISCORD_WEBHOOK_THUMBNAIL_URL").get(),
        footer_message=Secret("DISCORD_WEBHOOK_FOOTER_MESSAGE").get(),
        footer_icon_url=Secret("DISCORD_WEBHOOK_FOOTER_ICON_URL").get(),
        color=int(state.color[1:], 16), # Removes the #
        url=url
    )
    
    return embed

@curry
def discord_notifier(
    tracked_obj: Union["Flow", "Task"],
    old_state: State,
    new_state: State,
    ignore_states: list = None,
    only_states: list = None,
    webhook_secret: str = None,
    backend_info: bool = True,
    proxies: dict = None,
) -> State:
    """
    Discord state change handler; Works as a standalone state handler, or can be called from within a custom state handler.  
    This function is curried meaning that it can be called multiple times to partially bind any
    keyword arguments (see example below).
    Args:
        - tracked_obj (Task or Flow): Task or Flow object the handler is
            registered with
        - old_state (State): previous state of tracked object
        - new_state (State): new state of tracked object
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
    Returns:
        - State: the `new_state` object that was provided
    Raises:
        - ValueError: if the Discord notification fails for any reason
    Example:
        ```python
        from prefect import task
        from prefect_discord import discord_notifier
        @task(state_handlers=[discord_notifier(ignore_states=[Running])])
        def add(x, y):
            return x + y
        ```
    """
    webhook_url = cast(
        str, Secret(webhook_secret or "DISCORD_WEBHOOK_URL").get()
    )
    ignore_states = ignore_states or []
    only_states = only_states or []

    if any(isinstance(new_state, ignored) for ignored in ignore_states):
        return new_state

    if only_states and not any(
        [isinstance(new_state, included) for included in only_states]
    ):
        return new_state

    embed = discord_message_formatter(tracked_obj, new_state, backend_info)
    body = {"embeds": [embed]}

    r = requests.post(webhook_url, json=body, proxies=proxies)

    if not r.ok:
        raise ValueError("Discord notification for {} failed".format(tracked_obj))
    return new_state