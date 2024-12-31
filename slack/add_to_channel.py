"""Functionality to add users to channel."""
import json
import os
import pprint
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

load_dotenv()
pp = pprint.PrettyPrinter(indent=4, width=180)


@lru_cache
def get_known_users_file(workspace):
    """."""
    known_users_file = Path(f"generated/{workspace}_known_users.json")
    known_users_file.parent.mkdir(parents=True, exist_ok=True)
    return known_users_file


def get_known_users(workspace):
    """Load file with known users"""
    ret = {}
    known_users_file = get_known_users_file(workspace)
    if known_users_file.exists():
        try:
            with known_users_file.open(encoding="utf-8") as fobj:
                content = json.load(fobj)
                if content:
                    ret = content
        except json.decoder.JSONDecodeError:
            print(f"invalid json '{known_users_file}'")
    return ret


def save_known_users(workspace, users):
    """Cache users to limit the api calls."""
    if not users:
        raise ValueError("users required")
    with get_known_users_file(workspace).open('w', encoding="utf-8") as fobj:
        json.dump(users, fobj, indent=4)


def add_all_users_to_channel(workspace, channel_name='announcements'):
    """Add all the user in the workspace to the given channel."""
    if not workspace:
        raise ValueError("workspace is required")
    channel_id = os.getenv(f"{workspace}_ANNOUNCE_CHANNEL_ID".upper())
    token_name = f"{workspace}_OAUTH_TOKEN".upper()
    oauth_token = os.getenv(token_name)
    if not oauth_token:
        raise ValueError(f"{token_name} is required")

    client = WebClient(token=oauth_token)

    results = {"already_in_channel": [], "added": [], "skipped": []}
    known_users = get_known_users(workspace)
    try:
        print(f"Add users to channel {channel_name} ({channel_id}).")

        # Get the list of users in the workspace
        users_response = client.users_list()
        users = users_response['members']

        # Add each user to the channel
        for user in users:
            if str(user['id']) in known_users:
                results['skipped'].append(user['name'])
                continue
            known_users[str(user['id'])] = user
            if not user['is_bot'] and not user['deleted'] and user['name'] not in ('slackbot', 'bjhays'):
                try:
                    client.conversations_invite(channel=channel_id, users=user['id'])
                    results["added"].append(user['name'])
                except SlackApiError as e:
                    reason = e.response['error']
                    if reason not in results:
                        results[reason] = []
                    results[reason].append(user['name'])
        save_known_users(workspace, known_users)

    except SlackApiError as e:
        print(f"Slack API Error: {e.response['error']}")

    pp.pprint(results)
