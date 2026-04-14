#!/usr/bin/env python3
"""Send Discord confirmation after calendar events are created or canceled via gog."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "secrets.json"


def load_config():
    """Load secrets from config/secrets.json."""
    with open(CONFIG_PATH) as f:
        return json.load(f)


def get_event_details(event_id: str) -> dict:
    """Get calendar event details via gog."""
    result = subprocess.run(
        ["gog", "calendar", "event", event_id],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return {}
    
    # Parse gog output - format may vary
    output = result.stdout.strip()
    event = {"id": event_id}
    
    # Try to parse title from output
    for line in output.split("\n"):
        if "Title:" in line:
            event["title"] = line.split("Title:", 1)[1].strip()
        elif "Time:" in line:
            event["time"] = line.split("Time:", 1)[1].strip()
        elif "Location:" in line:
            event["location"] = line.split("Location:", 1)[1].strip()
    
    return event


def send_discord_embed(webhook_url: str, embed: dict) -> bool:
    """Send Discord embed via webhook."""
    import requests
    response = requests.post(
        webhook_url,
        json={"embeds": [embed]},
        headers={"Content-Type": "application/json"}
    )
    return response.status_code == 200


def send_event_confirmation(event_id: str) -> bool:
    """Send confirmation for event creation."""
    config = load_config()
    webhook_url = config.get("discord_webhook")
    
    if not webhook_url:
        print("ERROR: discord_webhook not configured")
        return False
    
    event = get_event_details(event_id)
    if not event:
        print(f"WARNING: Could not fetch event {event_id}, sending basic confirmation")
        title = "Calendar Event"
        time = "See your calendar"
        location = ""
    else:
        title = event.get("title", "Calendar Event")
        time = event.get("time", "See your calendar")
        location = event.get("location", "")
    
    embed = {
        "title": "📅 Event Created",
        "color": 5814783,  # Green
        "fields": [
            {"name": "Title", "value": title, "inline": False},
            {"name": "Time", "value": time, "inline": True},
        ],
        "footer": {"text": f"Event ID: {event_id}"}
    }
    
    if location:
        embed["fields"].append({"name": "Location", "value": location, "inline": True})
    
    success = send_discord_embed(webhook_url, embed)
    if success:
        print(f"CONFIRMATION: Event {event_id} creation notification sent")
    return success


def send_event_canceled(event_id: str) -> bool:
    """Send notification for event cancellation."""
    config = load_config()
    webhook_url = config.get("discord_webhook")
    
    if not webhook_url:
        print("ERROR: discord_webhook not configured")
        return False
    
    embed = {
        "title": "📅 Event Canceled",
        "color": 15158332,  # Red
        "description": "The following event has been removed:",
        "fields": [
            {"name": "Event ID", "value": event_id, "inline": False}
        ],
        "footer": {"text": "Check your calendar for details"}
    }
    
    success = send_discord_embed(webhook_url, embed)
    if success:
        print(f"CONFIRMATION: Event {event_id} cancellation notification sent")
    return success


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Send Discord notification for calendar events via gog"
    )
    parser.add_argument("--event-id", required=True, help="Calendar event ID")
    parser.add_argument(
        "--action",
        required=True,
        choices=["create", "cancel"],
        help="Action: create or cancel"
    )
    
    args = parser.parse_args()
    
    if args.action == "create":
        success = send_event_confirmation(args.event_id)
    else:
        success = send_event_canceled(args.event_id)
    
    sys.exit(0 if success else 1)