#!/usr/bin/env python3
"""
Notion Research Database - SEM-50
Create and manage Research database via Notion API
Uses synthetic data for testing when API is not configured.
"""
import os
import sys
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

# Configuration
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


def get_notion_token() -> Optional[str]:
    """Get Notion API token"""
    config = load_config()
    token = config.get('notion', {}).get('token')
    if not token:
        print("Warning: NOTION_TOKEN not found in config/secrets.json")
        print("Using synthetic mode for testing")
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


def create_research_database_schema() -> Dict[str, Any]:
    """Define Research database schema for SEM-50
    
    Schema:
    - Name (title) - Research title
    - Topic (select) - Category: AI, ML, Tech, Business, Market, Other
    - Source (url) - URL where research was found
    - Summary (rich_text) - Brief summary of findings
    - Date (date) - Date of research
    - Tags (multi_select) - Additional tags
    """
    return {
        'Name': {'title': {}},
        'Topic': {
            'select': {
                'options': [
                    {'name': 'AI', 'color': 'purple'},
                    {'name': 'ML', 'color': 'blue'},
                    {'name': 'Tech', 'color': 'green'},
                    {'name': 'Business', 'color': 'yellow'},
                    {'name': 'Market', 'color': 'orange'},
                    {'name': 'Other', 'color': 'gray'}
                ]
            }
        },
        'Source': {'url': {}},
        'Summary': {'rich_text': {}},
        'Date': {'date': {}},
        'Tags': {'multi_select': {}}
    }


def create_email_digest_database_schema() -> Dict[str, Any]:
    """Define Email Digest database schema for SEM-22
    
    Schema:
    - Name (title) - Email subject
    - Date (date) - Email received date
    - Urgency (select) - low, medium, high, critical
    - Summary (rich_text) - Brief summary of email
    - From (email) - Sender email
    """
    return {
        'Name': {'title': {}},
        'Date': {'date': {}},
        'Urgency': {
            'select': {
                'options': [
                    {'name': 'low', 'color': 'gray'},
                    {'name': 'medium', 'color': 'yellow'},
                    {'name': 'high', 'color': 'orange'},
                    {'name': 'critical', 'color': 'red'}
                ]
            }
        },
        'Summary': {'rich_text': {}},
        'From': {'email': {}}
    }


def create_database(parent_id: str, title: str, properties: Dict[str, Any]) -> Optional[Dict]:
    """Create a Notion database via API"""
    headers = get_headers()
    if not headers:
        return None
    
    import requests
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


def create_research_page(database_id: str, topic: str, source: str, 
                         summary: str, date: str, tags: List[str],
                         title: str) -> Optional[Dict]:
    """Create a research page entry"""
    headers = get_headers()
    if not headers:
        return None
    
    import requests
    payload = {
        'parent': {'database_id': database_id},
        'properties': {
            'Name': {'title': [{'text': {'content': title}}]},
            'Topic': {'select': {'name': topic}},
            'Source': {'url': source},
            'Summary': {'rich_text': [{'text': {'content': summary}}]},
            'Date': {'date': {'start': date}},
            'Tags': {'multi_select': [{'name': tag} for tag in tags]}
        }
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


# =============================================================================
# SYNTHETIC DATA TESTS (for when API is not configured)
# =============================================================================

def create_synthetic_research_entry() -> Dict[str, Any]:
    """Create a synthetic research entry for testing
    
    Returns example data structure showing what would be sent to Notion API
    """
    return {
        'parent': {'database_id': 'synthetic-research-db-id'},
        'properties': {
            'Name': {'title': [{'text': {'content': 'AI Startup Landscape 2026'}}]},
            'Topic': {'select': {'name': 'AI'}},
            'Source': {'url': 'https://example.com/ai-startup-research'},
            'Summary': {'rich_text': [{'text': {'content': 'Analysis of top 50 AI startups raising rounds in Q1 2026. Key trends include AI agents, code generation, and enterprise automation.'}}]},
            'Date': {'date': {'start': '2026-04-13'}},
            'Tags': {'multi_select': [{'name': 'startups'}, {'name': 'funding'}, {'name': 'AI'}]}
        }
    }


def create_synthetic_email_digest_entry() -> Dict[str, Any]:
    """Create a synthetic email digest entry for testing"""
    return {
        'parent': {'database_id': 'synthetic-email-digest-db-id'},
        'properties': {
            'Name': {'title': [{'text': {'content': 'Re: Urgent: Server Deployment Needed'}}]},
            'Date': {'date': {'start': '2026-04-13T09:30:00Z'}},
            'Urgency': {'select': {'name': 'high'}},
            'Summary': {'rich_text': [{'text': {'content': 'Infrastructure team needs approval for production deployment. Several blocked features depend on this.'}}]},
            'From': {'email': {'email': 'infra-team@company.com'}}
        }
    }


def test_synthetic_research_flow():
    """Test the research flow with synthetic data"""
    print("=" * 60)
    print("SEM-50: Research Database - Synthetic Test")
    print("=" * 60)
    
    # Test schema creation
    schema = create_research_database_schema()
    print("\n[1] Research Database Schema:")
    print(json.dumps(schema, indent=2))
    
    # Test entry creation
    entry = create_synthetic_research_entry()
    print("\n[2] Synthetic Research Entry:")
    print(json.dumps(entry, indent=2))
    
    print("\n[OK] Synthetic test completed successfully!")
    return True


def test_synthetic_email_digest_flow():
    """Test the email digest flow with synthetic data"""
    print("=" * 60)
    print("SEM-22: Email Digest Database - Synthetic Test")
    print("=" * 60)
    
    # Test schema creation
    schema = create_email_digest_database_schema()
    print("\n[1] Email Digest Database Schema:")
    print(json.dumps(schema, indent=2))
    
    # Test entry creation
    entry = create_synthetic_email_digest_entry()
    print("\n[2] Synthetic Email Digest Entry:")
    print(json.dumps(entry, indent=2))
    
    print("\n[OK] Synthetic test completed successfully!")
    return True


if __name__ == '__main__':
    test_synthetic_research_flow()
    print()
    test_synthetic_email_digest_flow()