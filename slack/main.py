"""."""
import argparse
import logging
import os
import pprint
from datetime import date, timedelta
from pathlib import Path

import requests
from dateutil import parser
from dotenv import dotenv_values

import add_to_channel
import translate

logger = logging.getLogger(__name__)
CONFIG = {
    **dotenv_values(".env"),  # load sensitive variables
    **os.environ,  # override loaded values with environment variables
}
pp = pprint.PrettyPrinter(indent=4)


def pull_and_read(ics_url, pull_new=True):
    """."""
    # download the ical
    if not ics_url:
        raise ValueError("ics_url is required!")
    cal_file_obj = Path("calendars/BSA_116_Activities.ics")
    cal_file_obj.parent.mkdir(parents=True, exist_ok=True)
    if pull_new:
        with cal_file_obj.open("w+", encoding="utf-8") as fobj:
            fobj.write(requests.get(ics_url, timeout=30).text)
    return translate.translate_ics(ics_file_obj=cal_file_obj)


def get_next_meeting(calendar_info, notify_types, weeks=1):
    """return the next meeting from calendar info."""
    today_date = date.today()
    next_monday = today_date + timedelta(days=-today_date.weekday(), weeks=weeks)
    print("Next Monday Date:", next_monday)
    possible_events = []
    for event in calendar_info:
        if event["types"] == []:
            continue
        if event["start"].startswith(str(next_monday)):
            possible_events.append(event)
        notify = False
        for ntype in notify_types:
            if ntype in event["types"]:
                notify = True
                break
        if not notify:
            continue
    return possible_events


class SlackGoatBot:
    """Goatbot sends messages to slack via slack webhook."""

    def __init__(self, cli_args):
        """Main!."""
        self.cli_args = cli_args
        hook_key = f"{cli_args.channel}_hook_url".upper()
        self.hook_url = CONFIG.get(hook_key)
        if not self.hook_url:
            raise ValueError(f"'{hook_key}' not found in .env")

        if cli_args.notify_meeting:
            calendar_info = pull_and_read(ics_url=CONFIG["TM_URL"])
            print(f"found {len(calendar_info)} calendar items")
            self.notify_next_meeting(calendar_info=calendar_info, weeks=cli_args.weeks)
        elif cli_args.add_announce:
            add_to_channel.add_all_users_to_channel()
        else:
            raise ValueError(f"invalid selection: {cli_args}")

    def notify_next_meeting(self, calendar_info, weeks=1):
        """Choose the next meeting and post to slack."""
        notify_types = ["h", "tm"]
        possible_events = get_next_meeting(
            calendar_info=calendar_info, notify_types=notify_types, weeks=weeks
        )
        if len(possible_events) != 1:
            raise ValueError(possible_events)
        self.send_message(possible_events[0])

    def send_message(self, event):
        """."""
        print("send message")
        pp.pprint(event)
        holiday = "h" in event["types"]
        meeting = "tm" in event["types"]
        t_minus = event["t-minus"]

        str_format = "%b %d @ %I:%M%p"
        if event["all_day"]:
            str_format = "%b %d"

        dt_str = parser.parse(event["start"]).strftime(str_format)
        msg = [":announcement:", str(dt_str), "-"]
        if holiday:
            msg.append("No Meeting:")
        else:
            msg.append("")

        attachments = []

        desc = event["description"]
        if meeting and desc:
            # green
            attachments.append(
                {
                    "color": "#008f29",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": "\n".join(desc)},
                        }
                    ],
                }
            )

        skillset = event["skillset"].strip()
        if (
            meeting
            and skillset
            and "".join(desc) != skillset
            and "coh" not in event["types"]
        ):
            # yellow
            attachments.append(
                {
                    "color": "#ffbd33",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": event["skillset"].strip(),
                            },
                        }
                    ],
                }
            )

        if meeting and t_minus and "coh" not in event["types"]:
            # grey
            attachments.append(
                {
                    "color": "#ffffff",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "\n - " + "\n - ".join(t_minus),
                            },
                        }
                    ],
                }
            )

        msg.append(event["title"])
        msg.append("<!channel>")

        msg = " ".join(msg)
        payload = {"text": msg, "attachments": attachments}
        logger.info("\n %s", pprint.pformat(payload, width=120))
        if self.cli_args.dry_run:
            logger.warning("dry run enabled, not sending to slack")
        else:
            requests.post(self.hook_url, json=payload, timeout=30)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.WARN,
        force=True,
        format="[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s",
    )
    arg_parser = argparse.ArgumentParser(description="Goat Bot!")

    arg_parser.add_argument(
        "-w", "--weeks", type=int, default=1, help="Number of weeks to notify on"
    )
    arg_parser.add_argument(
        "-nm",
        "--notify_meeting",
        action="store_true",
        help="Send notification about the next meeting",
    )
    arg_parser.add_argument(
        "-aa",
        "--add_announce",
        action="store_true",
        help="Add all users to #announcements",
    )
    arg_parser.add_argument(
        "-c",
        "--channel",
        default="goat-tester",
        help="Send notification to this channel (must have '<channel_name_lowercase>_hook_url' in your .env)",
    )

    arg_parser.add_argument(
        "--dry_run",
        action="store_true",
        help="dry run, don't send message",
    )

    args = arg_parser.parse_args()
    print(args)

    # add option to pull new... cli
    # add option for dry_run... don't sed message to announcements
    # add option to switch channels
    # option for # of weeks
    SlackGoatBot(args)
