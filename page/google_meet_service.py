import os
from google.oauth2 import service_account
from googleapiclient.discovery import build


def create_google_meet_event(summary, start_time, end_time,):
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'credentials.json')
    CALENDAR_ID = 'primary'

    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=creds)

    event = {
        'summary': summary,
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'Asia/Karachi',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'Asia/Karachi',
        },
        'conferenceData': {
            'createRequest': {
                'requestId': f"{start_time.isoformat()}-{summary}",
                'conferenceSolutionKey': {
                    'type': 'eventHangout'
                }
            }
        }
    }

    created_event = service.events().insert(
        calendarId=CALENDAR_ID,
        body=event,
        conferenceDataVersion=1
    ).execute()

    return created_event.get('hangoutLink')