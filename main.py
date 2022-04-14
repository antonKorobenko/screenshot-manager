import os
import time
import pickle
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apscheduler.schedulers.background import BackgroundScheduler


# Initialize background scheduler
SCHEDULER = BackgroundScheduler()
# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/calendar"]
# Relative path to credentials.json file
CREDENTIALS_FILE = "credentials.json"
# Location where screenshots will be located when not attending at any event
DEFAULT_SCREENSHOT_LOCATION = "/Users/{your username}/Desktop/"
# Sleep time represented in seconds before running kilall SystemUIServer
TIME_OFFSET = 3
# Pause before new API request for upcoming events
PERIOD = 15


def get_calendar_service():
    """
    Connect to Google Calendar service with @gmail.
    Returns a Construct a Resource for interacting with an API.
    The file token.pickle stores the user"s access and refresh tokens, and is
    created automatically when the authorization flow completes for the first
    time.
    """
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("calendar", "v3", credentials=creds)
    return service


def get_upcoming_events() -> list[dict]:
    """
    Request all upcoming events of current date from
    "primary" calendar. Returns a list of dictionaries.
    """
    service = get_calendar_service()

    # current time
    min_time = datetime.utcnow()
    # end of current date
    max_time = min_time.replace(
        hour=23, minute=59, second=59, microsecond=999999)
    # Call the Calendar API and get all future or current events
    calendars_result = service.events().list(
        calendarId="primary",
        timeMin=min_time.isoformat() + "Z",
        timeMax=max_time.isoformat() + "Z",
        singleEvents=True,
        orderBy="startTime").execute()
    return calendars_result.get("items", [])


def change_screenshot_location(new_location: str) -> None:
    # Change screenshot location
    command = f"defaults write com.apple.screencapture location {new_location}"
    os.system(command)
    # We need this so that changes are applied
    time.sleep(TIME_OFFSET)
    command = "killall SystemUIServer"
    os.system(command)


def prepare_screenshot_location(event_name="") -> None:
    """
    Change default scrrenshot folder based on received event name.
    NOTE: Works only for MacOS
    """
    new_screenshot_location = f"{DEFAULT_SCREENSHOT_LOCATION}/{event_name}"
    print(f"Screenshot location is {new_screenshot_location}")
    # Create folder if doesn't exisst
    if not os.path.exists(new_screenshot_location):
        os.mkdir(new_screenshot_location)
    change_screenshot_location(new_screenshot_location)


def scheduler_date(event_start: datetime, event_end: datetime, event_name: str) -> datetime | None:
    """ Get datetime for command execution """
    new_screenshot_location = DEFAULT_SCREENSHOT_LOCATION + "/" + event_name
    schedule_date = event_start - timedelta(seconds=TIME_OFFSET)
    now = datetime.now().astimezone()
    # first check if path already exists, otherwise, check if we're in middle of event
    if os.path.exists(new_screenshot_location):
        schedule_date = None
    elif event_start < now < event_end:
        schedule_date = now
    return schedule_date


def fetch_evets_and_schedule() -> None:
    """
    Iterate over upcoming events list and schedule commands execution.
    """
    events = get_upcoming_events()
    if not events:
        print("No upcoming events")

    for event in events:
        # extract main event properties
        event_start = datetime.strptime(
            event["start"].get("dateTime", event["start"].get("date")),
            "%Y-%m-%dT%H:%M:%S%z")
        event_end = datetime.strptime(
            event["end"].get("dateTime", event["end"].get("date")), 
            "%Y-%m-%dT%H:%M:%S%z")
        event_name = event["summary"].replace(" ", "_")
        # example of job_id: "2022-04-14 15:05-15:20 ZoomCall"
        job_id = "{} {}-{} {}".format(
            event_start.date(),
            str(event_start.time())[:5],
            str(event_end.time())[:5],
            event_name
        )
        # initialize folder name
        folder_name = "{}_{}".format(
            str(event_start)[:16].replace(" ", "_"),
            event_name
        )

        schedular_job = SCHEDULER.get_job(job_id)
        schedule_date = scheduler_date(event_start, event_end, event_name)

        if schedular_job is None and schedule_date is not None:
            print(f"Sceduling job for {job_id}")

            SCHEDULER.add_job(
                lambda: prepare_screenshot_location(folder_name),
                "date",
                run_date=schedule_date,
                id=job_id)
            
            # reset screenshot folder when event ends
            SCHEDULER.add_job(
                lambda: prepare_screenshot_location(),
                "date",
                run_date=event_end)
        time.sleep(2)
        print("#" * 30)


def main() -> None:
    # check for new events every PERIOD:int seconds
    SCHEDULER.add_job(
        fetch_evets_and_schedule,
        "interval",
        seconds=PERIOD,
        id="fetch_events_and_schedule"
        )
    SCHEDULER.start()


if __name__ == "__main__":
    main()
    try:
        # infinite loop
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        print("Closing Google Calendar Automation")
        print("Shutting down SCHEDULER")
        SCHEDULER.shutdown(wait=False)
        print("Default screenshot location")
        change_screenshot_location(DEFAULT_SCREENSHOT_LOCATION)
