#!/usr/bin/env python3
"""
Notion Integration Skill
Create and manage Notion pages for daily briefings
"""
import os
import sys
import json
import argparse
from datetime import datetime

NOTION_API_URL = 'https://api.notion.com/v1'
NOTION_VERSION = '2022-06-28'
CONFIG_PATH = 'config/secrets.json'


def load_config():
    """Load configuration from secrets file"""
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def get_notion_token():
    """Get Notion API token"""
    config = load_config()
    token = config.get('notion', {}).get('token')
    if not token:
        print("Error: NOTION_TOKEN not found in config/secrets.json")
        print("Get token from https://www.notion.so/my-integrations")
    return token


def get_headers():
    """Get Notion API headers"""
    token = get_notion_token()
    if not token:
        return None
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Notion-Version': NOTION_VERSION
    }


def create_database(parent_id, title, properties):
    """Create a Notion database"""
    headers = get_headers()
    if not headers:
        return None
    
    payload = {
        'parent': {'page_id': parent_id},
        'title': [{'text': {'content': title}}],
        'properties': properties
    }
    
    response = requests.post(
        f'{NOTION_API_URL}/databases',
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error creating database: {response.text}")
        return None


def create_page(database_id, properties):
    """Create a Notion page in a database"""
    headers = get_headers()
    if not headers:
        return None
    
    payload = {
        'parent': {'database_id': database_id},
        'properties': properties
    }
    
    response = requests.post(
        f'{NOTION_API_URL}/pages',
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error creating page: {response.text}")
        return None


def list_pages(database_id):
    """List pages in a database"""
    headers = get_headers()
    if not headers:
        return None
    
    payload = {
        'database_id': database_id,
        'page_size': 100
    }
    
    response = requests.post(
        f'{NOTION_API_URL}/databases/{database_id}/query',
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        return response.json().get('results', [])
    else:
        print(f"Error querying database: {response.text}")
        return None


def create_daily_briefing(date=None, email_summary="", calendar_summary="",
                          tasks_completed="", next_day_priorities=""):
    """Create a daily briefing page"""
    config = load_config()
    parent_id = config.get('notion', {}).get('daily_briefing_parent')
    
    if not parent_id:
        print("Error: daily_briefing_parent not set in config/secrets.json")
        return None
    
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    properties = {
        'Name': {'title': [{'text': {'content': f'Daily Briefing {date}'}}]},
        'Date': {'date': {'start': date}},
        'Email Summary': {'rich_text': [{'text': {'content': email_summary}}]},
        'Calendar Summary': {'rich_text': [{'text': {'content': calendar_summary}}]},
        'Tasks Completed': {'rich_text': [{'text': {'content': tasks_completed}}]},
        'Next Day Priorities': {'rich_text': [{'text': {'content': next_day_priorities}}]}
    }
    
    return create_page(parent_id, properties)


def init_daily_briefing_database(parent_id):
    """Initialize the Daily Briefing database with schema"""
    properties = {
        'Name': {'title': {}},
        'Date': {'date': {}},
        'Email Summary': {'rich_text': {}},
        'Calendar Summary': {'rich_text': {}},
        'Tasks Completed': {'rich_text': {}},
        'Next Day Priorities': {'rich_text': {}}
    }
    
    return create_database(parent_id, 'Daily Briefing', properties)


def cmd_create_briefing(args):
    """Create a daily briefing page"""
    result = create_daily_briefing(
        date=args.date,
        email_summary=args.email or "",
        calendar_summary=args.calendar or "",
        tasks_completed=args.tasks or "",
        next_day_priorities=args.priorities or ""
    )
    
    if result:
        print(f"Created briefing: {result.get('url')}")
        return 0
    return 1


def cmd_init_database(args):
    """Initialize Daily Briefing database"""
    if not args.parent:
        print("Error: --parent required (page ID)")
        return 1
    
    result = init_daily_briefing_database(args.parent)
    
    if result:
        print(f"Created database: {result.get('url')}")
        
        # Save parent ID to config
        config = load_config()
        if 'notion' not in config:
            config['notion'] = {}
        config['notion']['daily_briefing_parent'] = args.parent
        config['notion']['daily_briefing_database'] = result.get('id')
        
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Saved config to {CONFIG_PATH}")
        return 0
    return 1


def cmd_list_pages(args):
    """List pages in a database"""
    if not args.database:
        print("Error: --database required")
        return 1
    
    pages = list_pages(args.database)
    
    if pages is not None:
        print(f"\nPages in database ({len(pages)}):\n")
        for page in pages:
            props = page.get('properties', {})
            title = props.get('Name', {}).get('title', [{}])[0].get('text', {}).get('content', 'Untitled')
            date = props.get('Date', {}).get('date', {}).get('start', 'No date')
            print(f"  [{date}] {title}")
        return 0
    return 1


def main():
    parser = argparse.ArgumentParser(description='Notion Integration Skill')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Create briefing
    briefing_parser = subparsers.add_parser('create-briefing', help='Create daily briefing')
    briefing_parser.add_argument('--date', help='Date (YYYY-MM-DD)')
    briefing_parser.add_argument('--email', help='Email summary')
    briefing_parser.add_argument('--calendar', help='Calendar summary')
    briefing_parser.add_argument('--tasks', help='Tasks completed')
    briefing_parser.add_argument('--priorities', help='Next day priorities')
    
    # Init database
    init_parser = subparsers.add_parser('init-database', help='Initialize Daily Briefing database')
    init_parser.add_argument('--parent', required=True, help='Parent page ID')
    
    # List pages
    list_parser = subparsers.add_parser('list-pages', help='List pages in database')
    list_parser.add_argument('--database', required=True, help='Database ID')
    
    args = parser.parse_args()
    
    if args.command == 'create-briefing':
        return cmd_create_briefing(args)
    elif args.command == 'init-database':
        return cmd_init_database(args)
    elif args.command == 'list-pages':
        return cmd_list_pages(args)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    import requests
    sys.exit(main())