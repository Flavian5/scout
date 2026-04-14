#!/usr/bin/env python3
"""
email-alerts skill: Monitor Gmail for urgent emails and notify via Discord.
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CONFIG_DIR = PROJECT_ROOT / "config"
SECRETS_PATH = CONFIG_DIR / "secrets.json"


def load_config():
    """Load secrets config."""
    if SECRETS_PATH.exists():
        with open(SECRETS_PATH) as f:
            return json.load(f)
    return {}


def get_gog_emails(minutes=5):
    """Fetch recent unread emails via gog."""
    try:
        # Use newer_than with minutes
        result = subprocess.run(
            ["gog", "gmail", "messages", "search", 
             f"in:inbox is:unread newer_than:{minutes}m", 
             "--max", "20",
             "--json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0 and result.stdout:
            return json.loads(result.stdout)
    except Exception as e:
        print(f"Error fetching emails: {e}")
    return []


def is_urgent_email(email, config):
    """Check if email is urgent based on VIP senders, labels, keywords."""
    # Get VIP senders from config
    vip_senders = config.get("email_alerts", {}).get("vip_senders", [])
    keywords = config.get("email_alerts", {}).get("keywords", 
        ["urgent", "asap", "emergency", "important", "help", "critical"])
    
    # Check from address
    from_addr = email.get("from", "").lower()
    for vip in vip_senders:
        if vip.lower() in from_addr:
            return True, "VIP sender"
    
    # Check subject for keywords
    subject = email.get("subject", "").lower()
    for kw in keywords:
        if kw.lower() in subject:
            return True, f"Keyword: {kw}"
    
    # Check labels (starred, important)
    labels = email.get("labels", [])
    if any(label in ["STARRED", "IMPORTANT", "URGENT"] for label in labels):
        return True, "Label"
    
    return False, None


def send_discord_notification(webhook_url, email, urgency_reason):
    """Send Discord embed for urgent email."""
    import requests
    
    # Format timestamp
    sent_time = email.get("date", "")
    if sent_time:
        try:
            dt = datetime.fromisoformat(sent_time.replace("Z", "+00:00"))
            time_str = dt.strftime("%I:%M %p")
        except:
            time_str = sent_time[:16]
    else:
        time_str = datetime.now(timeformat="%I:%M %p").strftime("%I:%M %p")
    
    # Truncate body preview
    body = email.get("body", email.get("snippet", ""))[:200]
    
    payload = {
        "embeds": [{
            "title": f"📧 Urgent Email: {email.get('subject', '(no subject)')[:100]}",
            "color": 15158332,  # Red
            "fields": [
                {"name": "From", "value": email.get("from", "Unknown"), "inline": True},
                {"name": "Time", "value": time_str, "inline": True},
                {"name": "Reason", "value": urgency_reason, "inline": True},
            ],
            "description": body,
            "footer": {"text": "Scout Email Alert"}
        }]
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Discord notification error: {e}")
        return False


def check_and_notify():
    """Main function to check emails and send notifications."""
    config = load_config()
    webhook_url = config.get("discord_webhook")
    
    if not webhook_url:
        print("No discord_webhook configured in secrets.json")
        return
    
    # Fetch recent unread emails (last 30 minutes to catch any we might have missed)
    emails = get_gog_emails(minutes=30)
    
    if not emails:
        print("No unread emails found")
        return
    
    notified_count = 0
    for email in emails:
        is_urgent, reason = is_urgent_email(email, config)
        if is_urgent:
            success = send_discord_notification(webhook_url, email, reason)
            if success:
                print(f"✅ Notified: {email.get('subject', '')[:50]} - {reason}")
                notified_count += 1
            else:
                print(f"❌ Failed: {email.get('subject', '')[:50]}")
    
    print(f"Checked {len(emails)} emails, {notified_count} urgent notifications sent")


if __name__ == "__main__":
    check_and_notify()