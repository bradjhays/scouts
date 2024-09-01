# Slack "bot"
Using slack webhooks and an ical, post notifications to a given channel.

## Setup
1. copy the `sample.env` to `.env` and add the webhook url to your channel (talk to a slack admin for this)
2. setup (`python -m venv venv`) or enable a virtual env (`source venv/bin/activate`)
3. install requirements (`pip install -r requirements.txt`) and install dev requirements if you plan to contribute.

## Contribute
To contribute, open a PR against the repo from a fork.

 - make sure that `pre-commit run --all` is clean

## Options
`main.py` is our entry point for the bot.

```
$ python main.py --help
usage: main.py [-h] [-w WEEKS] [-nm] [-c CHANNEL] [--dry_run]

Goat Bot!

options:
  -h, --help            show this help message and exit
  -w WEEKS, --weeks WEEKS
                        Number of weeks to notify on
  -nm, --notify_meeting
                        Send notification about the next meeting
  -c CHANNEL, --channel CHANNEL
                        Send notification to this channel (must have '<channel_name_lowercase>_hook_url' in your .env)
  --dry_run             dry run, don't send message

```

## Cron
This bot runs on a linux system via a cron job.

Below are the currently configured jobs.
```
# Weekly Meetings - Post Tuesday @ 700 am pst
0 7 * * TUE     cd <path_to_repo> && SERVICE=slack OPTS=--notify_meeting --channel announcement docker-compose up
```
