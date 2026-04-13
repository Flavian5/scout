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
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
CREDENTIALS_PATH = 'config/calendar-credentials.json'
TOKEN_PATH = 'config/calendar-token.json'
DISCORD_WEBHOOK_PATH = 'config/secrets.json'
LOOKBACK_MINUTES = 0
MAX_RESULTS = 50
REMINDER_WINDOW = 15  # minutes

# In-memory cache to avoid duplicate reminders
REMINDER_CACHE_PATH = 'config/calendar-reminder-cache.json'


def load_secrets():
    """Load Discord webhook from secrets"""
    try:
        with open(DISCORD_WEBHOOK_PATH) as f:
            secrets = json.load(f)
            return secrets.get('discord_webhook', {}).get('url', '')
    except (FileNotFoundError, json.JSONDecodeError):
        return None


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


def authenticate():
    """Authenticate with Google Calendar API"""
    creds = None
    
    # Load existing token
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                print(f"Error: Credentials file not found at {CREDENTIALS_PATH}")
                print("Download OAuth client config from Google Cloud Console")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
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
    
    # Auth command
    auth_parser = subparsers.add_parser('auth', help='Authenticate with Google')
    auth_parser.add_argument('--credentials', help='Path to credentials file')
    
    args = parser.parse_args()
    
    if args.command == 'fetch' or args.command is None:
        return cmd_fetch(args)
    elif args.command == 'remind':
        return cmd_remind(args)
    elif args.command == 'auth':
        return cmd_auth(args)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())