#!/usr/bin/env python3
"""
Notion Integration Skill - SEM-94
Create and manage Notion pages for life management system.
Supports 8 databases: chores, financials, projects, weekend-plans,
daily-briefing, research, knowledge-base, deliverables
"""
import os
import sys
import json
import argparse
import requests
from datetime import datetime
from typing import Optional, Dict, Any, List

# Import schemas
from schemas import SCHEMAS, get_schema

NOTION_API_URL = 'https://api.notion.com/v1'
NOTION_VERSION = '2022-06-28'
CONFIG_PATH = 'config/secrets.json'


def load_config() -> Dict[str, Any]:
    """Load configuration from secrets file"""
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def get_notion_token() -> Optional[str]:
    """Get Notion API token"""
    config = load_config()
    token = config.get('notion', {}).get('token')
    if not token:
        print("Error: NOTION_TOKEN not found in config/secrets.json")
        print("Get token from https://www.notion.so/my-integrations")
    return token


def get_headers() -> Optional[Dict[str, str]]:
    """Get Notion API headers"""
    token = get_notion_token()
    if not token:
        return None
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Notion-Version': NOTION_VERSION
    }


def create_database(parent_id: str, title: str, properties: Dict[str, Any]) -> Optional[Dict]:
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


def create_page(database_id: str, properties: Dict[str, Any]) -> Optional[Dict]:
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


def query_database(database_id: str, filter_props: Optional[Dict] = None) -> Optional[List[Dict]]:
    """Query pages in a database with optional filters"""
    headers = get_headers()
    if not headers:
        return None
    
    payload = {
        'database_id': database_id,
        'page_size': 100
    }
    
    if filter_props:
        payload['filter'] = filter_props
    
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


def update_page(page_id: str, properties: Dict[str, Any]) -> Optional[Dict]:
    """Update a Notion page's properties"""
    headers = get_headers()
    if not headers:
        return None
    
    payload = {'properties': properties}
    
    response = requests.patch(
        f'{NOTION_API_URL}/pages/{page_id}',
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error updating page: {response.text}")
        return None


def list_pages(database_id: str) -> Optional[List[Dict]]:
    """List pages in a database"""
    return query_database(database_id)


# =============================================================================
# DATABASE INITIALIZATION COMMANDS
# =============================================================================

def init_database_by_name(db_name: str, parent_id: str) -> Optional[Dict]:
    """Initialize any database by name using schemas"""
    if db_name not in SCHEMAS:
        print(f"Error: Unknown database '{db_name}'")
        print(f"Available: {', '.join(SCHEMAS.keys())}")
        return None
    
    schema = get_schema(db_name)
    title = db_name.replace('-', ' ').title()
    
    return create_database(parent_id, title, schema)


# =============================================================================
# CREATE COMMANDS
# =============================================================================

def create_chore(name: str, frequency: str = 'one-off', days: List[str] = None,
                 due_date: str = None, recurring_time: str = 'anytime',
                 est_minutes: int = None, priority: str = 'should', notes: str = ""):
    """Create a chore entry"""
    config = load_config()
    db_id = config.get('notion', {}).get('chores_db')
    
    if not db_id:
        print("Error: chores_db not set in config/secrets.json")
        print("Run: python notion.py init-database chores --parent <page_id>")
        return None
    
    properties = {
        'Name': {'title': [{'text': {'content': name}}]},
        'Frequency': {'select': {'name': frequency}},
        'Status': {'select': {'name': 'todo'}},
        'Recurring Time': {'select': {'name': recurring_time}},
        'Priority': {'select': {'name': priority}},
    }
    
    if days:
        properties['Day(s)'] = {'multi_select': [{'name': d} for d in days]}
    
    if due_date:
        properties['Due Date'] = {'date': {'start': due_date}}
    
    if est_minutes:
        properties['Est. Minutes'] = {'number': est_minutes}
    
    if notes:
        properties['Notes'] = {'rich_text': [{'text': {'content': notes}}]}
    
    return create_page(db_id, properties)


def create_financial(name: str, category: str, subcategory: str, amount: float,
                     date: str = None, recurring: str = 'one-off',
                     budget_line: str = "", notes: str = ""):
    """Create a financial entry"""
    config = load_config()
    db_id = config.get('notion', {}).get('financials_db')
    
    if not db_id:
        print("Error: financials_db not set in config/secrets.json")
        print("Run: python notion.py init-database financials --parent <page_id>")
        return None
    
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    properties = {
        'Name': {'title': [{'text': {'content': name}}]},
        'Category': {'select': {'name': category}},
        'Subcategory': {'select': {'name': subcategory}},
        'Amount': {'number': amount},
        'Date': {'date': {'start': date}},
        'Recurring': {'select': {'name': recurring}},
    }
    
    if budget_line:
        properties['Budget Line'] = {'rich_text': [{'text': {'content': budget_line}}]}
    
    if notes:
        properties['Notes'] = {'rich_text': [{'text': {'content': notes}}]}
    
    return create_page(db_id, properties)


def create_project(name: str, status: str = 'planning', category: str = 'side-project',
                   start_date: str = None, target_end: str = None,
                   budget: float = None, notes: str = ""):
    """Create a project entry"""
    config = load_config()
    db_id = config.get('notion', {}).get('projects_db')
    
    if not db_id:
        print("Error: projects_db not set in config/secrets.json")
        print("Run: python notion.py init-database projects --parent <page_id>")
        return None
    
    properties = {
        'Name': {'title': [{'text': {'content': name}}]},
        'Status': {'select': {'name': status}},
        'Category': {'select': {'name': category}},
        'Progress': {'number': 0},
    }
    
    if start_date:
        properties['Start Date'] = {'date': {'start': start_date}}
    
    if target_end:
        properties['Target End'] = {'date': {'start': target_end}}
    
    if budget is not None:
        properties['Budget'] = {'number': budget}
    
    if notes:
        properties['Notes'] = {'rich_text': [{'text': {'content': notes}}]}
    
    return create_page(db_id, properties)


def create_weekend_plan(name: str, date: str = None, end_date: str = None,
                        location: str = "", people: List[str] = None,
                        status: str = 'idea', category: str = 'relaxation',
                        cost: float = None, notes: str = ""):
    """Create a weekend plan entry"""
    config = load_config()
    db_id = config.get('notion', {}).get('weekend_plans_db')
    
    if not db_id:
        print("Error: weekend_plans_db not set in config/secrets.json")
        print("Run: python notion.py init-database weekend-plans --parent <page_id>")
        return None
    
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    properties = {
        'Name': {'title': [{'text': {'content': name}}]},
        'Date': {'date': {'start': date}},
        'Status': {'select': {'name': status}},
        'Category': {'select': {'name': category}},
    }
    
    if end_date:
        properties['End Date'] = {'date': {'start': end_date}}
    
    if location:
        properties['Location'] = {'rich_text': [{'text': {'content': location}}]}
    
    if people:
        properties['People'] = {'multi_select': [{'name': p} for p in people]}
    
    if cost is not None:
        properties['Cost'] = {'number': cost}
    
    if notes:
        properties['Notes'] = {'rich_text': [{'text': {'content': notes}}]}
    
    return create_page(db_id, properties)


def create_daily_briefing(date: str = None, email_summary: str = "",
                          calendar_summary: str = "", tasks_completed: str = "",
                          next_day_priorities: str = "", urgent_tickets: str = ""):
    """Create a daily briefing page"""
    config = load_config()
    parent_id = config.get('notion', {}).get('daily_briefing_parent')
    
    if not parent_id:
        print("Error: daily_briefing_parent not set in config/secrets.json")
        print("Run: python notion.py init-database daily-briefing --parent <page_id>")
        return None
    
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    properties = {
        'Name': {'title': [{'text': {'content': f'Daily Briefing {date}'}}]},
        'Date': {'date': {'start': date}},
        'Email Summary': {'rich_text': [{'text': {'content': email_summary}}]},
        'Calendar Summary': {'rich_text': [{'text': {'content': calendar_summary}}]},
        'Tasks Completed': {'rich_text': [{'text': {'content': tasks_completed}}]},
        'Next Day Priorities': {'rich_text': [{'text': {'content': next_day_priorities}}]},
        'Urgent Tickets': {'rich_text': [{'text': {'content': urgent_tickets}}]}
    }
    
    return create_page(parent_id, properties)


def create_research(title: str, topic: str, source: str = "",
                    summary: str = "", date: str = None,
                    tags: List[str] = None, relevance: str = 'Medium'):
    """Create a research entry"""
    config = load_config()
    db_id = config.get('notion', {}).get('research_db')
    
    if not db_id:
        print("Error: research_db not set in config/secrets.json")
        print("Run: python notion.py init-database research --parent <page_id>")
        return None
    
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    properties = {
        'Name': {'title': [{'text': {'content': title}}]},
        'Topic': {'select': {'name': topic}},
        'Summary': {'rich_text': [{'text': {'content': summary}}]},
        'Date': {'date': {'start': date}},
        'Relevance': {'select': {'name': relevance}},
    }
    
    if source:
        properties['Source'] = {'url': source}
    
    if tags:
        properties['Tags'] = {'multi_select': [{'name': t} for t in tags]}
    
    return create_page(db_id, properties)


def create_knowledge_entry(name: str, category: str, content: str = "",
                           tags: List[str] = None):
    """Create a knowledge base entry"""
    config = load_config()
    db_id = config.get('notion', {}).get('knowledge_base_db')
    
    if not db_id:
        print("Error: knowledge_base_db not set in config/secrets.json")
        print("Run: python notion.py init-database knowledge-base --parent <page_id>")
        return None
    
    properties = {
        'Name': {'title': [{'text': {'content': name}}]},
        'Category': {'select': {'name': category}},
        'Content': {'rich_text': [{'text': {'content': content}}]},
        'Last Updated': {'date': {'start': datetime.now().strftime('%Y-%m-%d')}},
    }
    
    if tags:
        properties['Tags'] = {'multi_select': [{'name': t} for t in tags]}
    
    return create_page(db_id, properties)


def create_deliverable(name: str, deliverable_type: str = 'Document',
                       status: str = 'Draft', linear_ticket: str = "",
                       due_date: str = None, description: str = "",
                       tags: List[str] = None):
    """Create a deliverable entry"""
    config = load_config()
    db_id = config.get('notion', {}).get('deliverables_db')
    
    if not db_id:
        print("Error: deliverables_db not set in config/secrets.json")
        print("Run: python notion.py init-database deliverables --parent <page_id>")
        return None
    
    properties = {
        'Name': {'title': [{'text': {'content': name}}]},
        'Type': {'select': {'name': deliverable_type}},
        'Status': {'select': {'name': status}},
    }
    
    if linear_ticket:
        properties['Linear Ticket'] = {'url': linear_ticket}
    
    if due_date:
        properties['Due Date'] = {'date': {'start': due_date}}
    
    if description:
        properties['Description'] = {'rich_text': [{'text': {'content': description}}]}
    
    if tags:
        properties['Tags'] = {'multi_select': [{'name': t} for t in tags]}
    
    return create_page(db_id, properties)


# =============================================================================
# COMMAND HANDLERS
# =============================================================================

def cmd_init_database(args) -> int:
    """Initialize any database by name"""
    db_name = args.database
    
    if not args.parent:
        print("Error: --parent required (page ID)")
        return 1
    
    result = init_database_by_name(db_name, args.parent)
    
    if result:
        print(f"Created database: {result.get('url')}")
        
        # Save database ID to config
        config = load_config()
        if 'notion' not in config:
            config['notion'] = {}
        
        # Map database name to config key
        config_key = f"{db_name.replace('-', '_')}_db"
        config['notion'][config_key] = result.get('id')
        config['notion'][f"{db_name.replace('-', '_')}_parent"] = args.parent
        
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Saved config to {CONFIG_PATH}")
        return 0
    return 1


def cmd_create_chore_handler(args) -> int:
    """Create a chore entry"""
    days = args.days.split(',') if args.days else None
    
    result = create_chore(
        name=args.name,
        frequency=args.frequency or 'one-off',
        days=days,
        due_date=args.due_date,
        recurring_time=args.time or 'anytime',
        est_minutes=args.minutes,
        priority=args.priority or 'should',
        notes=args.notes or ""
    )
    
    if result:
        print(f"Created chore: {result.get('url')}")
        return 0
    return 1


def cmd_create_financial_handler(args) -> int:
    """Create a financial entry"""
    result = create_financial(
        name=args.name,
        category=args.category,
        subcategory=args.subcategory,
        amount=args.amount,
        date=args.date,
        recurring=args.recurring or 'one-off',
        budget_line=args.budget_line or "",
        notes=args.notes or ""
    )
    
    if result:
        print(f"Created financial entry: {result.get('url')}")
        return 0
    return 1


def cmd_create_project_handler(args) -> int:
    """Create a project entry"""
    result = create_project(
        name=args.name,
        status=args.status or 'planning',
        category=args.category or 'side-project',
        start_date=args.start_date,
        target_end=args.target_end,
        budget=args.budget,
        notes=args.notes or ""
    )
    
    if result:
        print(f"Created project: {result.get('url')}")
        return 0
    return 1


def cmd_create_weekend_handler(args) -> int:
    """Create a weekend plan entry"""
    people = args.people.split(',') if args.people else None
    
    result = create_weekend_plan(
        name=args.name,
        date=args.date,
        end_date=args.end_date,
        location=args.location or "",
        people=people,
        status=args.status or 'idea',
        category=args.category or 'relaxation',
        cost=args.cost,
        notes=args.notes or ""
    )
    
    if result:
        print(f"Created weekend plan: {result.get('url')}")
        return 0
    return 1


def cmd_create_briefing(args) -> int:
    """Create a daily briefing page"""
    result = create_daily_briefing(
        date=args.date,
        email_summary=args.email or "",
        calendar_summary=args.calendar or "",
        tasks_completed=args.tasks or "",
        next_day_priorities=args.priorities or "",
        urgent_tickets=args.tickets or ""
    )
    
    if result:
        print(f"Created briefing: {result.get('url')}")
        return 0
    return 1


def cmd_create_research_handler(args) -> int:
    """Create a research entry"""
    tags = args.tags.split(',') if args.tags else None
    
    result = create_research(
        title=args.title,
        topic=args.topic,
        source=args.source or "",
        summary=args.summary or "",
        date=args.date,
        tags=tags,
        relevance=args.relevance or 'Medium'
    )
    
    if result:
        print(f"Created research entry: {result.get('url')}")
        return 0
    return 1


def cmd_create_knowledge_handler(args) -> int:
    """Create a knowledge base entry"""
    tags = args.tags.split(',') if args.tags else None
    
    result = create_knowledge_entry(
        name=args.name,
        category=args.category,
        content=args.content or "",
        tags=tags
    )
    
    if result:
        print(f"Created knowledge entry: {result.get('url')}")
        return 0
    return 1


def cmd_create_deliverable_handler(args) -> int:
    """Create a deliverable entry"""
    tags = args.tags.split(',') if args.tags else None
    
    result = create_deliverable(
        name=args.name,
        deliverable_type=args.type or 'Document',
        status=args.status or 'Draft',
        linear_ticket=args.linear or "",
        due_date=args.due_date,
        description=args.description or "",
        tags=tags
    )
    
    if result:
        print(f"Created deliverable: {result.get('url')}")
        return 0
    return 1


def cmd_list_pages(args) -> int:
    """List pages in a database"""
    if not args.database:
        # Try to get from config
        config = load_config()
        db_name = args.name
        config_key = f"{db_name.replace('-', '_')}_db"
        args.database = config.get('notion', {}).get(config_key)
        
        if not args.database:
            print(f"Error: Database '{db_name}' not found in config")
            print("Initialize with: python notion.py init-database <name> --parent <page_id>")
            return 1
    
    pages = list_pages(args.database)
    
    if pages is not None:
        print(f"\nPages in database ({len(pages)}):\n")
        for page in pages:
            props = page.get('properties', {})
            title = props.get('Name', {}).get('title', [{}])[0].get('text', {}).get('content', 'Untitled')
            # Try to get date from common date fields
            date = (props.get('Date', {}).get('date', {}).get('start') or
                    props.get('Start Date', {}).get('date', {}).get('start') or
                    'No date')
            print(f"  [{date}] {title}")
        return 0
    return 1


def cmd_query(args) -> int:
    """Query database with optional filters"""
    config = load_config()
    db_name = args.name
    config_key = f"{db_name.replace('-', '_')}_db"
    db_id = config.get('notion', {}).get(config_key)
    
    if not db_id:
        print(f"Error: Database '{db_name}' not found in config")
        print("Initialize with: python notion.py init-database <name> --parent <page_id>")
        return 1
    
    filter_props = None
    if args.filter:
        # Parse filter as simple property:value format
        parts = args.filter.split(':')
        if len(parts) == 2:
            prop, value = parts
            filter_props = {
                'property': prop,
                prop.replace(' ', '_'): {'select': {'name': value}}
            }
    
    pages = query_database(db_id, filter_props)
    
    if pages is not None:
        print(f"\nQuery results ({len(pages)} pages):\n")
        for page in pages:
            props = page.get('properties', {})
            title = props.get('Name', {}).get('title', [{}])[0].get('text', {}).get('content', 'Untitled')
            print(f"  - {title}")
        return 0
    return 1


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Notion Integration Skill - Life Management System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available databases:
  chores, financials, projects, weekend-plans
  daily-briefing, research, knowledge-base, deliverables

Examples:
  # Initialize a database
  python notion.py init-database chores --parent <page_id>

  # Create a chore
  python notion.py create-chore "Weekly laundry" --frequency weekly --days "Sunday"

  # List pages
  python notion.py list-pages --name chores
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Init database (any type)
    init_parser = subparsers.add_parser('init-database', help='Initialize a database')
    init_parser.add_argument('database', help='Database name (e.g., chores, financials)')
    init_parser.add_argument('--parent', required=True, help='Parent page ID')
    
    # Create commands
    chore_parser = subparsers.add_parser('create-chore', help='Create a chore')
    chore_parser.add_argument('--name', required=True, help='Chore name')
    chore_parser.add_argument('--frequency', choices=['daily', 'weekly', 'monthly', 'one-off'])
    chore_parser.add_argument('--days', help='Comma-separated days (e.g., "Mon,Sun")')
    chore_parser.add_argument('--due-date', help='Due date (YYYY-MM-DD)')
    chore_parser.add_argument('--time', choices=['morning', 'afternoon', 'evening', 'anytime'])
    chore_parser.add_argument('--minutes', type=int, help='Estimated minutes')
    chore_parser.add_argument('--priority', choices=['must', 'should', 'nice-to-have'])
    chore_parser.add_argument('--notes', help='Additional notes')
    
    financial_parser = subparsers.add_parser('create-financial', help='Create a financial entry')
    financial_parser.add_argument('--name', required=True, help='Entry name')
    financial_parser.add_argument('--category', required=True,
                                  choices=['income', 'expense', 'savings', 'investment', 'debt'])
    financial_parser.add_argument('--subcategory', required=True,
                                  choices=['housing', 'food', 'transport', 'utilities', 'fun', 'health', 'tech', 'other'])
    financial_parser.add_argument('--amount', required=True, type=float, help='Amount')
    financial_parser.add_argument('--date', help='Date (YYYY-MM-DD)')
    financial_parser.add_argument('--recurring', choices=['monthly', 'biweekly', 'one-off'])
    financial_parser.add_argument('--budget-line', help='Budget line description')
    financial_parser.add_argument('--notes', help='Additional notes')
    
    project_parser = subparsers.add_parser('create-project', help='Create a project')
    project_parser.add_argument('--name', required=True, help='Project name')
    project_parser.add_argument('--status', choices=['planning', 'active', 'paused', 'done', 'abandoned'])
    project_parser.add_argument('--category', choices=['home', 'career', 'health', 'learning', 'side-project'])
    project_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    project_parser.add_argument('--target-end', help='Target end date (YYYY-MM-DD)')
    project_parser.add_argument('--budget', type=float, help='Budget amount')
    project_parser.add_argument('--notes', help='Additional notes')
    
    weekend_parser = subparsers.add_parser('create-weekend', help='Create a weekend plan')
    weekend_parser.add_argument('--name', required=True, help='Plan name')
    weekend_parser.add_argument('--date', help='Start date (YYYY-MM-DD)')
    weekend_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    weekend_parser.add_argument('--location', help='Location')
    weekend_parser.add_argument('--people', help='Comma-separated people')
    weekend_parser.add_argument('--status', choices=['idea', 'planned', 'confirmed', 'done', 'canceled'])
    weekend_parser.add_argument('--category', choices=['outdoor', 'social', 'errands', 'relaxation', 'travel'])
    weekend_parser.add_argument('--cost', type=float, help='Estimated cost')
    weekend_parser.add_argument('--notes', help='Additional notes')
    
    briefing_parser = subparsers.add_parser('create-briefing', help='Create daily briefing')
    briefing_parser.add_argument('--date', help='Date (YYYY-MM-DD)')
    briefing_parser.add_argument('--email', help='Email summary')
    briefing_parser.add_argument('--calendar', help='Calendar summary')
    briefing_parser.add_argument('--tasks', help='Tasks completed')
    briefing_parser.add_argument('--priorities', help='Next day priorities')
    briefing_parser.add_argument('--tickets', help='Urgent tickets')
    
    research_parser = subparsers.add_parser('create-research', help='Create research entry')
    research_parser.add_argument('--title', required=True, help='Research title')
    research_parser.add_argument('--topic', required=True,
                                  choices=['AI', 'ML', 'Tech', 'Business', 'Market', 'Other'])
    research_parser.add_argument('--source', help='Source URL')
    research_parser.add_argument('--summary', help='Summary')
    research_parser.add_argument('--date', help='Date (YYYY-MM-DD)')
    research_parser.add_argument('--tags', help='Comma-separated tags')
    research_parser.add_argument('--relevance', choices=['High', 'Medium', 'Low'])
    
    knowledge_parser = subparsers.add_parser('create-knowledge', help='Create knowledge entry')
    knowledge_parser.add_argument('--name', required=True, help='Entry name')
    knowledge_parser.add_argument('--category', required=True,
                                   choices=['architecture', 'setup', 'api', 'troubleshooting', 'reference'])
    knowledge_parser.add_argument('--content', help='Content')
    knowledge_parser.add_argument('--tags', help='Comma-separated tags')
    
    deliverable_parser = subparsers.add_parser('create-deliverable', help='Create deliverable')
    deliverable_parser.add_argument('--name', required=True, help='Deliverable name')
    deliverable_parser.add_argument('--type', choices=['Document', 'Code', 'Research', 'Design', 'Other'])
    deliverable_parser.add_argument('--status', choices=['Draft', 'In Review', 'Published', 'Archived'])
    deliverable_parser.add_argument('--linear', help='Linear ticket URL')
    deliverable_parser.add_argument('--due-date', help='Due date (YYYY-MM-DD)')
    deliverable_parser.add_argument('--description', help='Description')
    deliverable_parser.add_argument('--tags', help='Comma-separated tags')
    
    # List pages
    list_parser = subparsers.add_parser('list-pages', help='List pages in database')
    list_parser.add_argument('--database', help='Database ID')
    list_parser.add_argument('--name', help='Database name (from config)')
    
    # Query
    query_parser = subparsers.add_parser('query', help='Query database with filters')
    query_parser.add_argument('name', help='Database name')
    query_parser.add_argument('--filter', help='Filter as property:value')
    
    args = parser.parse_args()
    
    if args.command == 'init-database':
        return cmd_init_database(args)
    elif args.command == 'create-chore':
        return cmd_create_chore_handler(args)
    elif args.command == 'create-financial':
        return cmd_create_financial_handler(args)
    elif args.command == 'create-project':
        return cmd_create_project_handler(args)
    elif args.command == 'create-weekend':
        return cmd_create_weekend_handler(args)
    elif args.command == 'create-briefing':
        return cmd_create_briefing(args)
    elif args.command == 'create-research':
        return cmd_create_research_handler(args)
    elif args.command == 'create-knowledge':
        return cmd_create_knowledge_handler(args)
    elif args.command == 'create-deliverable':
        return cmd_create_deliverable_handler(args)
    elif args.command == 'list-pages':
        return cmd_list_pages(args)
    elif args.command == 'query':
        return cmd_query(args)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())