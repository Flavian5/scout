#!/usr/bin/env python3
"""
Google Calendar Check Skill
Check upcoming events and send meeting reminders via Discord
"""
import os
import sys
import json
import argparse
from datetime import datetime, timezone, timedelta

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    print("Error: google-auth libraries not installed")
    print("Run: pip install google-auth google-auth-oauthlib google-api-python-client")
    sys.exit(1)

# Configuration
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/calendar.events']
CREDENTIALS_PATH = 'config/calendar-credentials.json'
TOKEN_PATH = 'config/calendar-token.json'
SECRETS_PATH = 'config/secrets.json'
LOOKBACK_MINUTES = 0
MAX_RESULTS = 50
REMINDER_WINDOW = 15  # minutes

# In-memory cache to avoid duplicate reminders
REMINDER_CACHE_PATH = 'config/calendar-reminder-cache.json'


def load_secrets():
    """Load Discord webhook and LLM config from secrets"""
    try:
        with open(SECRETS_PATH) as f:
            secrets = json.load(f)
            discord_url = secrets.get('discord_webhook', '')
            llm_config = secrets.get('llm_api', {})
            return {
                'discord_webhook': discord_url,
                'llm_api': llm_config
            }
    except (FileNotFoundError, json.JSONDecodeError):
        return {'discord_webhook': None, 'llm_api': {}}


def load_reminder_cache():
    """Load cached reminder timestamps to avoid duplicates"""
    try:
        with open(REMINDER_CACHE_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"reminded": {}}


def save_reminder_cache(cache):
    """Save reminder cache"""
    os.makedirs(os.path.dirname(REMINDER_CACHE_PATH), exist_ok=True)
    with open(REMINDER_CACHE_PATH, 'w') as f:
        json.dump(cache, f)


def authenticate(readonly=False):
    """Authenticate with Google Calendar API
    
    Args:
        readonly: If True, only requests read-only scope
    """
    scopes = ['https://www.googleapis.com/auth/calendar.readonly']
    if not readonly:
        scopes.append('https://www.googleapis.com/auth/calendar.events')
    
    creds = None
    
    # Load existing token
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, scopes)
    
    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                print(f"Error: Credentials file not found at {CREDENTIALS_PATH}")
                print("Download OAuth client config from Google Cloud Console")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, scopes)
            creds = flow.run_local_server(port=0)
        
        # Save token
        os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
        with open(TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())
    
    return build('calendar', 'v3', credentials=creds)


def fetch_events(service, lookback_minutes=LOOKBACK_MINUTES, max_results=MAX_RESULTS):
    """Fetch upcoming calendar events"""
    now = datetime.now(timezone.utc)
    time_min = now - timedelta(minutes=lookback_minutes)
    
    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min.isoformat(),
        maxResults=max_results,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    
    result = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        
        # Parse start time
        if 'T' in start:
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
        else:
            start_dt = datetime.fromisoformat(start)
        
        # Calculate minutes until event
        minutes_until = int((start_dt - now).total_seconds() / 60)
        
        result.append({
            'id': event['id'],
            'title': event.get('summary', 'Untitled'),
            'start': start,
            'end': end,
            'location': event.get('location', ''),
            'attendees': [a.get('email', '') for a in event.get('attendees', [])],
            'minutes_until': minutes_until
        })
    
    return result


def send_discord_reminder(event, webhook_url):
    """Send meeting reminder to Discord"""
    import requests
    
    # Format time
    start = event['start']
    if 'T' in start:
        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
        time_str = start_dt.strftime('%I:%M %p')
    else:
        time_str = start
    
    # Build location text
    location = event.get('location', '')
    if location:
        if 'meet.google.com' in location:
            location_text = f"[Join Meeting]({location})"
        elif location.startswith('http'):
            location_text = f"[Join]({location})"
        else:
            location_text = location
    else:
        location_text = "No location"
    
    # Attendees
    attendees = event.get('attendees', [])
    attendees_text = f"{len(attendees)} attendee(s)" if attendees else "No attendees"
    
    embed = {
        "title": f"📅 Meeting in {event['minutes_until']} minutes",
        "description": f"**{event['title']}**\n\n🕐 {time_str}\n📍 {location_text}\n👥 {attendees_text}",
        "color": 5814783,  # Green
        "footer": {"text": "Scout Calendar Reminder"}
    }
    
    payload = {"embeds": [embed]}
    
    try:
        requests.post(webhook_url, json=payload, timeout=10)
        return True
    except Exception as e:
        print(f"Error sending Discord notification: {e}")
        return False


def send_reminders(events, webhook_url):
    """Check for events starting soon and send reminders"""
    cache = load_reminder_cache()
    reminded_count = 0
    
    for event in events:
        minutes = event['minutes_until']
        
        # Check if within reminder window
        if 0 < minutes <= REMINDER_WINDOW:
            event_id = event['id']
            
            # Check if already reminded (within last 15 min)
            last_reminded = cache['reminded'].get(event_id)
            if last_reminded:
                last_time = datetime.fromisoformat(last_reminded)
                if datetime.now(timezone.utc) - last_time < timedelta(minutes=15):
                    continue  # Already reminded
            
            # Send reminder
            if send_discord_reminder(event, webhook_url):
                cache['reminded'][event_id] = datetime.now(timezone.utc).isoformat()
                reminded_count += 1
                print(f"Reminded: {event['title']} (in {minutes} min)")
    
    if reminded_count > 0:
        save_reminder_cache(cache)
    
    return reminded_count


def parse_natural_language_request(request_text):
    """Parse natural language event request using LLM (SEM-30).
    
    Converts phrases like "meeting with john at 3pm tomorrow" into event details.
    """
    secrets = load_secrets()
    llm_config = secrets.get('llm_api', {})
    
    if not llm_config.get('api_key'):
        print("[SYNTHETIC] No LLM configured - using synthetic parsing")
        return parse_synthetic_request(request_text)
    
    prompt = f"""Parse this calendar request and extract event details.

Request: "{request_text}"

Extract:
- title: What is the meeting about (be concise, max 50 chars)
- date: ISO format date (YYYY-MM-DD) or relative like "tomorrow", "next Monday"
- time: ISO format time (HH:MM) in 24h format, or relative like "3pm", "midnight"
- duration_minutes: Estimated duration in minutes (default 30)
- location: Any location mentioned, or "Google Meet" if video call mentioned

Respond ONLY with valid JSON like:
{{"title": "Team sync", "date": "2026-04-14", "time": "15:00", "duration_minutes": 30, "location": "Google Meet"}}"""
    
    import requests
    
    headers = {
        "Authorization": f"Bearer {llm_config.get('api_key')}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": llm_config.get('model', 'MiniMax-M2.7'),
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "temperature": 0.1,
    }
    
    try:
        response = requests.post(
            llm_config.get('endpoint', 'https://api.minimax.io/v1/text/chatcompletion_v2'),
            headers=headers,
            json=payload,
            timeout=30
        )
        result = response.json()
        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        # Extract JSON from response
        import re
        json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"[ERROR] LLM parsing failed: {e}")
    
    return parse_synthetic_request(request_text)


def parse_synthetic_request(request_text):
    """Synthetic parsing for testing when LLM is not available"""
    text = request_text.lower()
    
    # Simple keyword-based parsing for testing
    title = request_text
    date = "tomorrow"
    time = "14:00"
    duration = 30
    location = "Google Meet"
    
    # Extract time patterns
    import re
    time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', text)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
        if time_match.group(3) == 'pm' and hour != 12:
            hour += 12
        time = f"{hour:02d}:{minute:02d}"
    
    return {
        "title": title,
        "date": date,
        "time": time,
        "duration_minutes": duration,
        "location": location
    }


def create_calendar_event(service, event_details):
    """Create a calendar event (SEM-31).
    
    Args:
        service: Authenticated Google Calendar service
        event_details: Dict with title, date, time, duration_minutes, location
    
    Returns:
        Created event dict or None
    """
    from datetime import datetime, timedelta
    
    # Parse date and time
    date_str = event_details.get('date', 'tomorrow')
    time_str = event_details.get('time', '14:00')
    
    # Convert relative date to actual date
    today = datetime.now().date()
    if date_str == 'tomorrow':
        start_date = today + timedelta(days=1)
    elif date_str == 'today':
        start_date = today
    else:
        try:
            start_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = today + timedelta(days=1)
    
    # Parse time
    try:
        hour, minute = map(int, time_str.split(':'))
        start_datetime = datetime.combine(start_date, datetime.min.time().replace(hour=hour, minute=minute))
    except ValueError:
        start_datetime = datetime.combine(start_date, datetime.min.time().replace(hour=14, minute=0))
    
    # End time
    duration = event_details.get('duration_minutes', 30)
    end_datetime = start_datetime + timedelta(minutes=duration)
    
    # Build event
    event = {
        'summary': event_details.get('title', 'New Event'),
        'start': {
            'dateTime': start_datetime.isoformat(),
            'timeZone': 'America/Toronto',
        },
        'end': {
            'dateTime': end_datetime.isoformat(),
            'timeZone': 'America/Toronto',
        },
    }
    
    location = event_details.get('location', '')
    if location:
        event['location'] = location
    
    # Create event
    try:
        created_event = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
        return created_event
    except Exception as e:
        print(f"[ERROR] Failed to create calendar event: {e}")
        return None


def confirm_event_via_discord(event, webhook_url):
    """Confirm event creation via Discord (SEM-32).
    
    Args:
        event: The created Google Calendar event
        webhook_url: Discord webhook URL
    """
    import requests
    
    start = event.get('start', {})
    end = event.get('end', {})
    
    # Parse start time
    start_dt_str = start.get('dateTime', start.get('date', ''))
    if 'T' in start_dt_str:
        start_dt = datetime.fromisoformat(start_dt_str.replace('Z', '+00:00'))
        time_str = start_dt.strftime('%B %d, %Y at %I:%M %p')
    else:
        time_str = start_dt_str
    
    # Parse end time
    end_dt_str = end.get('dateTime', end.get('date', ''))
    if 'T' in end_dt_str:
        end_dt = datetime.fromisoformat(end_dt_str.replace('Z', '+00:00'))
        end_time_str = end_dt.strftime('%I:%M %p')
    else:
        end_time_str = ''
    
    location = event.get('location', 'No location')
    if location.startswith('http'):
        location_text = f"[Join Meeting]({location})"
    else:
        location_text = location
    
    embed = {
        "title": "✅ Calendar Event Created",
        "description": f"**{event.get('summary', 'New Event')}**\n\n🗓️ {time_str}\n📍 {location_text}",
        "color": 3066993,  # Green
        "footer": {"text": "Scout Calendar"}
    }
    
    payload = {
        "content": "📅 New calendar event has been created!",
        "embeds": [embed]
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code in (200, 204):
            print("[OK] Event confirmation sent to Discord")
            return True
        else:
            print(f"[ERROR] Discord webhook failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Failed to send Discord confirmation: {e}")
        return False


def cmd_create(args):
    """Create a calendar event from natural language (SEM-30, SEM-31, SEM-32)"""
    if not args.request:
        print("Error: --request required (e.g., 'meeting with john at 3pm tomorrow')")
        return 1
    
    # Parse natural language request
    print(f"Parsing: \"{args.request}\"")
    event_details = parse_natural_language_request(args.request)
    print(f"Parsed: {json.dumps(event_details, indent=2)}")
    
    # Create event
    service = authenticate(readonly=False)
    if not service:
        print("[SYNTHETIC] Would create event with details:")
        print(json.dumps(event_details, indent=2))
        return 0
    
    event = create_calendar_event(service, event_details)
    if not event:
        print("[ERROR] Failed to create event")
        return 1
    
    print(f"[OK] Created event: {event.get('htmlLink')}")
    
    # Confirm via Discord
    secrets = load_secrets()
    webhook = secrets.get('discord_webhook')
    if webhook:
        confirm_event_via_discord(event, webhook)
    else:
        print("[SYNTHETIC] Would send Discord confirmation")
    
    return 0


def print_events(events):
    """Pretty print events"""
    if not events:
        print("No upcoming events")
        return
    
    print(f"\nUpcoming Events ({len(events)}):\n")
    for event in events:
        minutes = event['minutes_until']
        if minutes < 0:
            time_str = f"{abs(minutes)} min ago"
        elif minutes == 0:
            time_str = "Now"
        else:
            time_str = f"in {minutes} min"
        
        location = event.get('location', '')
        print(f"  [{time_str}] {event['title']}")
        if location:
            print(f"           📍 {location}")
    print()


def cmd_fetch(args):
    """Fetch and display events"""
    service = authenticate()
    if not service:
        return 1
    
    events = fetch_events(service)
    
    if args.json:
        print(json.dumps({"events": events, "count": len(events)}))
    else:
        print_events(events)
    
    # Send reminders if requested
    if args.remind:
        webhook = load_secrets()
        if webhook:
            reminded = send_reminders(events, webhook)
            if reminded > 0 and not args.json:
                print(f"Sent {reminded} reminder(s)")
        else:
            print("Warning: Discord webhook not configured")
    
    return 0


def cmd_remind(args):
    """Send reminders for upcoming events"""
    service = authenticate()
    if not service:
        return 1
    
    webhook = load_secrets()
    if not webhook:
        print("Error: Discord webhook not configured")
        return 1
    
    events = fetch_events(service)
    reminded = send_reminders(events, webhook)
    print(f"Sent {reminded} reminder(s)")
    
    return 0


def cmd_auth(args):
    """Authenticate with Google"""
    creds_path = args.credentials or CREDENTIALS_PATH
    if not os.path.exists(creds_path):
        print(f"Error: Credentials file not found at {creds_path}")
        print("Download OAuth client config from Google Cloud Console")
        return 1
    
    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
    creds = flow.run_local_server(port=0)
    
    os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
    with open(TOKEN_PATH, 'w') as f:
        f.write(creds.to_json())
    
    print("Authentication successful!")
    return 0


def main():
    parser = argparse.ArgumentParser(description='Google Calendar Check Skill')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Fetch command
    fetch_parser = subparsers.add_parser('fetch', help='Fetch upcoming events')
    fetch_parser.add_argument('--json', action='store_true', help='Output JSON')
    fetch_parser.add_argument('--remind', action='store_true', help='Send reminders')
    
    # Remind command
    subparsers.add_parser('remind', help='Send meeting reminders')
    
    # Create command (SEM-30, SEM-31, SEM-32)
    create_parser = subparsers.add_parser('create', help='Create event from natural language')
    create_parser.add_argument('--request', required=True, help='Natural language request (e.g., "meeting with john at 3pm tomorrow")')
    
    # Auth command
    auth_parser = subparsers.add_parser('auth', help='Authenticate with Google')
    auth_parser.add_argument('--credentials', help='Path to credentials file')
    
    args = parser.parse_args()
    
    if args.command == 'fetch' or args.command is None:
        return cmd_fetch(args)
    elif args.command == 'remind':
        return cmd_remind(args)
    elif args.command == 'create':
        return cmd_create(args)
    elif args.command == 'auth':
        return cmd_auth(args)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())