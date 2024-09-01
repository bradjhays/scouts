"""Translate ics to json."""
import json
import logging
import pprint
import re
from datetime import datetime
from pathlib import Path

import jicson
import pytz
from dateutil import parser

logger = logging.getLogger(__name__)

pp = pprint.PrettyPrinter()

# EVENT_TYPES = {
#     "c": "campout",
#     "o": "outing",
#     "d": "day outing",
#     "do": "day outing",
#     "f": "fundraiser",
#     "s": "service",
#     "h": "holiday",
#     "?": "not sure on dates",
# }

known_meetings = {
    "Troop Meeting": "tm",
    "PLC": "plc",
    "No Troop Mtg": "no",
    "holiday": "h",
    "Court Of Honor": "coh",
    "coh": "coh"
}

# t_minus_types = ["c", "o", "d", "do", "f", "s"]



def event_type(event_str):
    """."""
    type_regex = r"\[([a-z\?]{1,2})\]"  # r"^\[([a-z]+)\]\ "
    etypes = re.findall(type_regex, str(event_str), re.IGNORECASE | re.MULTILINE)
    logger.info("%s from '%s'", etypes, event_str)
    clean = event_str
    if etypes:
        for etype in etypes:
            logger.info("removing [%s]", etype)
            clean = clean.replace(f"[{etype}]", "")
    if clean:
        for known, abbr in known_meetings.items():
            logger.info("check '%s' in %s", known, clean.lower())
            if known.lower() in clean.lower():
                etypes.append(abbr)
                # leave the knowns alone
                # insensitive = re.compile(re.escape(known), re.IGNORECASE)
                # clean = insensitive.sub('', clean).replace("[]", "")

    else:
        raise ValueError(event_str)

    ret = []
    for abr in etypes:
        # if we want full names
        # if len(abr) <= 2 and abr in EVENT_TYPES:
        #     ret.append(EVENT_TYPES[abr])
        # elif abr not in EVENT_TYPES:
        #     raise Exception(f"'{abr}' not in {EVENT_TYPES.keys()} for '{event_str}'")
        # else:
        ret.append(abr.lower())

    return clean, ret


def get_theme(description):
    """."""
    if not description:
        return (None, None)
    reg = r"Theme:[ ]?(.*?)\."
    theme = re.findall(reg, description, re.MULTILINE)
    try:
        theme = theme[0]
    except IndexError:
        theme = None
    if not theme:
        theme = None
    logger.info("Theme: %s from '%s'", theme, description)
    return theme


def get_skillset(description):
    """."""
    reg = r"Skillset:(.*)T-minus"
    matches = re.findall(reg, description, re.MULTILINE | re.IGNORECASE)
    if matches:
        return matches[0]

    logger.debug("'%s' has no skillset", description)
    return None


def get_t_minus(description):
    """."""
    ret = []
    reg = r"T-minus:(.*)"
    matches = re.findall(reg, description, re.MULTILINE | re.IGNORECASE)
    if matches:
        logger.info(" => %s", matches[0].strip())
        for line in matches[0].split('\\n'):
            if line.lstrip().startswith('-') and len(line.strip()) > 1:
                line = line.lstrip()[1:].lstrip().title()
                ret.append(line)
        # raise ValueError(description)
        return sorted(ret)
    logger.debug("'%s' has no t_minus", description)
    return ret


def clean_ics(file_obj):
    """jicson can't handle descriptions with new lines."""
    # do something better? not os specific?
    new = ""
    regex = r"\n^\ "
    with file_obj.open(encoding="utf-8") as fobj:
        new = fobj.read()
    return re.sub(regex, '', new, 0, re.MULTILINE)


def clean_desc(description):
    """."""
    # remove unicode
    description = description.encode("ascii", "ignore").decode()
    description = description.replace("null.","")

    if description.startswith("."):
        description = description.replace(".", "", 1).strip()
    return description


def get_dates(event):
    """."""
    all_day = False
    end = ""
    if "DTEND" in event:
        end = parser.parse(event["DTEND"]).astimezone(tz=None)
    elif "DTEND;VALUE=DATE" in event:
        # full day event
        end = parser.parse(event["DTEND;VALUE=DATE"]).astimezone(tz=None)
        logger.info(end)
        all_day = True
    else:
        raise ValueError(f"no end time {event}")

    start = ""
    # Has start/end time
    if "DTSTART" in event:
        start = parser.parse(event["DTSTART"]).astimezone(tz=None)

    elif "DTSTART;VALUE=DATE" in event:
        # full day event
        start = parser.parse(event["DTSTART;VALUE=DATE"]).astimezone()
        logger.info(start)
        all_day = True
    else:
        raise ValueError(f"no start time {event}")

    if all_day:
        end = start

    return start, end, all_day



def cleaner(string):
    """."""
    if string:
        string = string.replace("\\n", "").replace("\\", "").replace("  ", "").replace("\n", "")
        string = string.strip().lstrip()
    return string


def description_leftovers(description):
    """."""
    if description and "Theme" in description:
        ret = []
        description = description.replace("Remarks: ", "").replace("Description: ", "")
        if "----------" in description:
            ret = []
            for line in description.split("----------")[0].split('\\n'):
                if line.strip():
                    ret.append(line.replace('\\', ""))

        else:
            for line in description.rstrip().split('\\n'):
                if line.strip():
                    ret.append(line.replace('\\', ""))


        description = ret
        # raise ValueError(description)

    return description



def translate_ics(ics_file_obj):
    """."""
    # read from file
    result = jicson.fromText(clean_ics(ics_file_obj))
    result = result["VCALENDAR"][0]["VEVENT"]
    new_res = []
    for event in result:
        # desc = None
        # setypes = []
        # etypes = []
        description = event.get("DESCRIPTION")
        if description:
            description = clean_desc(description.replace("\n", ""))
        title = event["SUMMARY"]
        title, event_types = event_type(title)
        start, end, all_day = get_dates(event)
        new = {
            "title": title.strip(),
            "location": event.get("LOCATION"),
            "types": event_types,
            "theme": cleaner(get_theme(description)),
            "skillset": cleaner(get_skillset(description)),
            "raw": description,
            "t-minus": get_t_minus(description),
            "start": str(start),
            "end": str(end),
            "all_day": all_day
        }
        new["description"] = description_leftovers(description=description)

        # don't process past items... waste time
        if end < datetime.now().astimezone(pytz.timezone("US/Pacific")):
            logger.info("!!!! %s < %s skipping '%s'", end, datetime.now(), new['title'])
            continue

        logger.info("--- %s %s ---",new['start'] ,new['title'])
        new_res.append(new)

    data_file_obj = Path("generated/data.json")
    with data_file_obj.open("w", encoding="utf-8") as fobj:
        json.dump(new_res, fobj, indent=4)

    return new_res
