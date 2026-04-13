#!/usr/bin/env python3
"""
Email Check Skill - Gmail inbox monitoring with urgency classification.

Fetches unread emails from last 24h, classifies urgency using LLM,
sends urgent alerts via WhatsApp, and pushes digest to Notion.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Config paths
CONFIG_DIR = PROJECT_ROOT / "config"
GMAIL_TOKEN_PATH = CONFIG_DIR / "gmail-token.json"
GMAIL_CREDENTIALS_PATH = CONFIG_DIR / "gmail-credentials.json"
SECRETS_PATH = CONFIG_DIR / "secrets.json"

# Gmail API scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]


def load_config():
    """Load secrets config."""
    if SECRETS_PATH.exists():
        with open(SECRETS_PATH) as f:
            return json.load(f)
    return {}


def get_llm_config():
    """Get LLM config from secrets."""
    config = load_config()
    llm = config.get("llm_api", {})
    return {
        "api_key": llm.get("api_key", os.environ.get("MINIMAX_API_KEY", "")),
        "endpoint": llm.get("endpoint", "https://api.minimax.io/v1/text/chatcompletion_v2"),
        "model": llm.get("model", "MiniMax-M2.7"),
    }


def call_minimax_llm(api_key, endpoint, model, messages, temperature=0.3, max_tokens=2000):
    """Call MiniMax LLM using native REST API."""
    import requests

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "temperature": temperature,
        "top_p": 0.95,
    }

    response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
    result = response.json()
    choices = result.get("choices", [])
    if choices and len(choices) > 0:
        return choices[0].get("message", {}).get("content", "")
    return ""


def authenticate_oauth():
    """Authenticate with Gmail API using OAuth2."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    if not GMAIL_CREDENTIALS_PATH.exists():
        print(f"Error: Credentials file not found at {GMAIL_CREDENTIALS_PATH}")
        print("Download OAuth2 credentials from Google Cloud Console")
        return None

    flow = InstalledAppFlow.from_client_secrets_file(
        str(GMAIL_CREDENTIALS_PATH), SCOPES
    )
    creds = flow.run_local_server(port=0)

    # Save token
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(GMAIL_TOKEN_PATH, "w") as f:
        f.write(creds.to_json())

    print(f"Token saved to {GMAIL_TOKEN_PATH}")
    return creds


def get_gmail_service():
    """Get authenticated Gmail service."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = None

    if GMAIL_TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(GMAIL_TOKEN_PATH, "w") as f:
                f.write(creds.to_json())
        else:
            print("No valid credentials. Run with --auth first.")
            return None

    return build("gmail", "v1", credentials=creds)


def fetch_unread_emails(service, lookback_hours=24, max_results=50):
    """Fetch unread emails from last N hours."""
    from googleapiclient.errors import HttpError

    # Calculate query time
    query_time = datetime.now() - timedelta(hours=lookback_hours)
    query_str = f"is:unread after:{query_time.strftime('%Y/%m/%d')}"

    try:
        results = (
            service.users()
            .messages()
            .list(
                userId="me",
                q=query_str,
                maxResults=max_results,
            )
            .execute()
        )

        messages = results.get("messages", [])
        emails = []

        for msg in messages:
            msg_data = service.users().messages().get(userId="me", id=msg["id"]).execute()
            headers = msg_data.get("payload", {}).get("headers", [])

            sender = ""
            subject = ""
            for header in headers:
                if header["name"].lower() == "from":
                    sender = header["value"]
                elif header["name"].lower() == "subject":
                    subject = header["value"]

            # Get snippet
            snippet = msg_data.get("snippet", "")

            # Get timestamp
            internal_date = int(msg_data.get("internalDate", "0"))
            timestamp = datetime.fromtimestamp(internal_date / 1000).isoformat() + "Z"

            emails.append({
                "id": msg["id"],
                "sender": sender,
                "subject": subject,
                "snippet": snippet,
                "timestamp": timestamp,
            })

        return {"emails": emails, "count": len(emails)}

    except HttpError as error:
        print(f"Gmail API error: {error}")
        return {"emails": [], "count": 0, "error": str(error)}


def classify_urgency(email, llm_config):
    """Classify email urgency using LLM."""
    prompt = f"""Classify this email as urgent, important, or routine.

Email:
- From: {email['sender']}
- Subject: {email['subject']}
- Preview: {email['snippet']}

Rules:
- urgent = needs immediate attention (crisis, time-sensitive, critical)
- important = should respond today (boss, client, deadlines)
- routine = can wait (newsletters, notifications, low priority)

Respond with ONLY one word: urgent, important, or routine."""

    messages = [{"role": "user", "content": prompt}]
    result = call_minimax_llm(
        api_key=llm_config["api_key"],
        endpoint=llm_config["endpoint"],
        model=llm_config["model"],
        messages=messages,
        temperature=0.1,
    )

    result = result.strip().lower()
    if "urgent" in result:
        return "urgent"
    elif "important" in result:
        return "important"
    return "routine"


def classify_all_emails(emails, llm_config):
    """Classify urgency for all emails."""
    classified = []
    urgent_count = 0
    important_count = 0
    routine_count = 0

    for email in emails:
        urgency = classify_urgency(email, llm_config)
        email["urgency"] = urgency

        if urgency == "urgent":
            urgent_count += 1
        elif urgency == "important":
            important_count += 1
        else:
            routine_count += 1

        classified.append(email)

    return {
        "emails": classified,
        "summary": {
            "urgent": urgent_count,
            "important": important_count,
            "routine": routine_count,
        },
    }


def send_urgent_whatsapp_alert(urgent_emails):
    """Send WhatsApp alert for urgent emails."""
    # Placeholder - integrate with whatsapp-bridge skill
    print(f"Would send WhatsApp alert for {len(urgent_emails)} urgent emails:")
    for email in urgent_emails:
        print(f"  - {email['subject']} from {email['sender']}")


def push_to_notion_digest(emails):
    """Push email digest to Notion database."""
    # Placeholder - integrate with Notion MCP
    print(f"Would push {len(emails)} emails to Notion Email Digest database")


def main():
    parser = argparse.ArgumentParser(description="Email Check Skill")
    parser.add_argument("--auth", action="store_true", help="Authenticate with Gmail")
    parser.add_argument("--fetch", action="store_true", help="Fetch unread emails")
    parser.add_argument("--classify", action="store_true", help="Classify email urgency")
    parser.add_argument("--urgent-alert", action="store_true", help="Send urgent alerts via WhatsApp")
    parser.add_argument("--push-notion", action="store_true", help="Push digest to Notion")
    parser.add_argument("--hours", type=int, default=24, help="Hours to look back (default: 24)")
    parser.add_argument("--max", type=int, default=50, help="Max emails to fetch (default: 50)")

    args = parser.parse_args()

    if args.auth:
        print("Starting OAuth2 authentication...")
        creds = authenticate_oauth()
        if creds:
            print("Authentication successful!")
        return

    if args.fetch or args.classify or args.urgent_alert or args.push_notion:
        print("Connecting to Gmail...")
        service = get_gmail_service()
        if not service:
            return

        print(f"Fetching unread emails from last {args.hours} hours...")
        result = fetch_unread_emails(service, lookback_hours=args.hours, max_results=args.max)
        emails = result.get("emails", [])

        if not emails:
            print("No unread emails found.")
            return

        print(f"Found {len(emails)} unread emails")

        if args.classify:
            print("Classifying urgency...")
            llm_config = get_llm_config()
            if not llm_config["api_key"]:
                print("Error: No LLM API key configured")
                return

            result = classify_all_emails(emails, llm_config)
            emails = result["emails"]

            print("\nClassification Summary:")
            print(f"  Urgent: {result['summary']['urgent']}")
            print(f"  Important: {result['summary']['important']}")
            print(f"  Routine: {result['summary']['routine']}")

            # Save classified emails
            output_path = PROJECT_ROOT / "data" / "email_fetch.json"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(result, f, indent=2)
            print(f"\nResults saved to {output_path}")

        if args.urgent_alert:
            urgent_emails = [e for e in emails if e.get("urgency") == "urgent"]
            if urgent_emails:
                send_urgent_whatsapp_alert(urgent_emails)
            else:
                print("No urgent emails to alert.")

        if args.push_notion:
            push_to_notion_digest(emails)

        return

    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()