"""Calendar Tools."""
import pprint
import datetime
import logging

NOW = datetime.datetime.now()
CURRENT_MONTH = int(NOW.month)
CURRENT_YEAR = int(NOW.year)
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 
	'July', 'August', 'September', 'October', 'November', 'December']
pp = pprint.PrettyPrinter(indent=4, width=200)
logger = logging.getLogger(__name__)


def troop_reminders(events, notify_types, months=2):
	"""print a list of events as follows for x months
	Month Name
	date	event name
	Month Name 2
	date	event name

	Meeting Date 1
	<list all t-minus>
	Meeting Date 1
	<list all t-minus>
	"""

	monthly = {}
	t_minus = {}

	for event in events:
		# logger.info(event)
		# 2025-01-03
		_, month, day = event['start'].split(' ', maxsplit=1)[0].split('-')
		_, _, end_day = event['end'].split(' ', maxsplit=1)[0].split('-')
		if int(month) not in range(CURRENT_MONTH, CURRENT_MONTH + months + 1):
			# skip months we don't want
			logger.info(f"{int(month)} != {CURRENT_MONTH}, {month} in range({CURRENT_MONTH}, {CURRENT_MONTH + months})")
			continue
		if month not in monthly:
			monthly[month] = []
		if day != end_day:
			day = f"{day}-{end_day}"
		monthly[month].append(f"{day}\t{event['title']}")

		for event_type in notify_types:
			if event_type in event['types']:
				logger.info("add t-minus info")
				logger.info(event)
				t_minus[f"{month}/{day}"] = event["t-minus"]


	# pp.pprint(monthly)

	for month, months_events in monthly.items():
		if not months_events:
			continue
		print(MONTHS[int(month)])
		for event_line in months_events:
			print(event_line)

	pp.pprint(t_minus)
	for meeting, t_schedule in t_minus.items():
		if not t_schedule:
			continue
		print(meeting)
		print("-" + "\n-".join(t_schedule).replace(f"/{CURRENT_YEAR}", ""))
