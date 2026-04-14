#!/usr/bin/env python3
"""
Notion Database Schemas - SEM-94
All 8 life management database schemas for the Notion integration.
"""
from typing import Dict, Any


# =============================================================================
# CHORES DATABASE
# =============================================================================

def chores_schema() -> Dict[str, Any]:
    """Chores database schema for recurring and one-off tasks.
    
    Use cases:
    - "add chore: weekly laundry on Sunday"
    - "what chores are due today?"
    - "mark laundry as done"
    """
    return {
        'Name': {'title': {}},
        'Frequency': {
            'select': {
                'options': [
                    {'name': 'daily', 'color': 'blue'},
                    {'name': 'weekly', 'color': 'green'},
                    {'name': 'monthly', 'color': 'yellow'},
                    {'name': 'one-off', 'color': 'gray'}
                ]
            }
        },
        'Day(s)': {'multi_select': {}},
        'Status': {
            'select': {
                'options': [
                    {'name': 'todo', 'color': 'red'},
                    {'name': 'done', 'color': 'green'},
                    {'name': 'skipped', 'color': 'gray'}
                ]
            }
        },
        'Due Date': {'date': {}},
        'Recurring Time': {
            'select': {
                'options': [
                    {'name': 'morning', 'color': 'orange'},
                    {'name': 'afternoon', 'color': 'yellow'},
                    {'name': 'evening', 'color': 'purple'},
                    {'name': 'anytime', 'color': 'gray'}
                ]
            }
        },
        'Est. Minutes': {'number': {'format': 'number'}},
        'Priority': {
            'select': {
                'options': [
                    {'name': 'must', 'color': 'red'},
                    {'name': 'should', 'color': 'orange'},
                    {'name': 'nice-to-have', 'color': 'blue'}
                ]
            }
        },
        'Last Done': {'date': {}},
        'Notes': {'rich_text': {}}
    }


# =============================================================================
# FINANCIALS DATABASE
# =============================================================================

def financials_schema() -> Dict[str, Any]:
    """Financials database schema for income/expense tracking.
    
    Use cases:
    - "logged $50 groceries"
    - "budget status this month"
    - "track spending by category"
    """
    return {
        'Name': {'title': {}},
        'Category': {
            'select': {
                'options': [
                    {'name': 'income', 'color': 'green'},
                    {'name': 'expense', 'color': 'red'},
                    {'name': 'savings', 'color': 'blue'},
                    {'name': 'investment', 'color': 'purple'},
                    {'name': 'debt', 'color': 'orange'}
                ]
            }
        },
        'Subcategory': {
            'select': {
                'options': [
                    {'name': 'housing', 'color': 'gray'},
                    {'name': 'food', 'color': 'yellow'},
                    {'name': 'transport', 'color': 'blue'},
                    {'name': 'utilities', 'color': 'green'},
                    {'name': 'fun', 'color': 'pink'},
                    {'name': 'health', 'color': 'red'},
                    {'name': 'tech', 'color': 'purple'},
                    {'name': 'other', 'color': 'gray'}
                ]
            }
        },
        'Amount': {'number': {'format': 'dollar'}},
        'Date': {'date': {}},
        'Recurring': {
            'select': {
                'options': [
                    {'name': 'monthly', 'color': 'blue'},
                    {'name': 'biweekly', 'color': 'yellow'},
                    {'name': 'one-off', 'color': 'gray'}
                ]
            }
        },
        'Budget Line': {'rich_text': {}},
        'Receipt': {'url': {}},
        'Notes': {'rich_text': {}}
    }


# =============================================================================
# PROJECTS DATABASE
# =============================================================================

def projects_schema() -> Dict[str, Any]:
    """Projects database schema for long-term project tracking.
    
    Use cases:
    - "how's the kitchen renovation going?"
    - "project status: career pivot"
    - "track milestones and budget"
    """
    return {
        'Name': {'title': {}},
        'Status': {
            'select': {
                'options': [
                    {'name': 'planning', 'color': 'gray'},
                    {'name': 'active', 'color': 'blue'},
                    {'name': 'paused', 'color': 'yellow'},
                    {'name': 'done', 'color': 'green'},
                    {'name': 'abandoned', 'color': 'red'}
                ]
            }
        },
        'Category': {
            'select': {
                'options': [
                    {'name': 'home', 'color': 'green'},
                    {'name': 'career', 'color': 'blue'},
                    {'name': 'health', 'color': 'red'},
                    {'name': 'learning', 'color': 'purple'},
                    {'name': 'side-project', 'color': 'yellow'}
                ]
            }
        },
        'Start Date': {'date': {}},
        'Target End': {'date': {}},
        'Actual End': {'date': {}},
        'Budget': {'number': {'format': 'dollar'}},
        'Spent': {'number': {'format': 'dollar'}},
        'Progress': {'number': {'format': 'percent'}},
        'Next Milestone': {'rich_text': {}},
        'Notes': {'rich_text': {}}
    }


# =============================================================================
# WEEKEND PLANS DATABASE
# =============================================================================

def weekend_plans_schema() -> Dict[str, Any]:
    """Weekend Plans database schema for planning weekend activities.
    
    Use cases:
    - "plan something fun for Saturday"
    - "what's on this weekend?"
    - "add weekend plan: hiking with friends"
    """
    return {
        'Name': {'title': {}},
        'Date': {'date': {}},
        'End Date': {'date': {}},
        'Location': {'rich_text': {}},
        'People': {'multi_select': {}},
        'Status': {
            'select': {
                'options': [
                    {'name': 'idea', 'color': 'gray'},
                    {'name': 'planned', 'color': 'blue'},
                    {'name': 'confirmed', 'color': 'green'},
                    {'name': 'done', 'color': 'green'},
                    {'name': 'canceled', 'color': 'red'}
                ]
            }
        },
        'Category': {
            'select': {
                'options': [
                    {'name': 'outdoor', 'color': 'green'},
                    {'name': 'social', 'color': 'blue'},
                    {'name': 'errands', 'color': 'yellow'},
                    {'name': 'relaxation', 'color': 'purple'},
                    {'name': 'travel', 'color': 'orange'}
                ]
            }
        },
        'Cost': {'number': {'format': 'dollar'}},
        'Notes': {'rich_text': {}}
    }


# =============================================================================
# DAILY BRIEFING DATABASE
# =============================================================================

def daily_briefing_schema() -> Dict[str, Any]:
    """Daily Briefing database schema for daily summaries.
    
    Use cases:
    - "summarize my day"
    - "show yesterday's briefing"
    - aggregated from email + calendar + tasks
    """
    return {
        'Name': {'title': {}},
        'Date': {'date': {}},
        'Email Summary': {'rich_text': {}},
        'Calendar Summary': {'rich_text': {}},
        'Tasks Completed': {'rich_text': {}},
        'Next Day Priorities': {'rich_text': {}},
        'Urgent Tickets': {'rich_text': {}}
    }


# =============================================================================
# RESEARCH DATABASE (from research_db.py)
# =============================================================================

def research_schema() -> Dict[str, Any]:
    """Research database schema for web research tracking.
    
    Use cases:
    - "archive this research about X"
    - "find my research on AI agents"
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
        'Tags': {'multi_select': {}},
        'Relevance': {
            'select': {
                'options': [
                    {'name': 'High', 'color': 'green'},
                    {'name': 'Medium', 'color': 'yellow'},
                    {'name': 'Low', 'color': 'gray'}
                ]
            }
        }
    }


# =============================================================================

# KNOWLEDGE BASE DATABASE
# =============================================================================

def knowledge_base_schema() -> Dict[str, Any]:
    """Knowledge Base database schema for reference documentation.
    
    Use cases:
    - "how do I set up the dev environment?"
    - "document the API integration"
    - "find troubleshooting guides"
    """
    return {
        'Name': {'title': {}},
        'Category': {
            'select': {
                'options': [
                    {'name': 'architecture', 'color': 'blue'},
                    {'name': 'setup', 'color': 'green'},
                    {'name': 'api', 'color': 'purple'},
                    {'name': 'troubleshooting', 'color': 'red'},
                    {'name': 'reference', 'color': 'gray'}
                ]
            }
        },
        'Content': {'rich_text': {}},
        'Last Updated': {'date': {}},
        'Tags': {'multi_select': {}}
    }


# =============================================================================
# DELIVERABLES DATABASE
# =============================================================================

def deliverables_schema() -> Dict[str, Any]:
    """Deliverables database schema for work outputs.
    
    Use cases:
    - "log this document as a deliverable"
    - "track research deliverables"
    - linked to Linear tickets
    """
    return {
        'Name': {'title': {}},
        'Type': {
            'select': {
                'options': [
                    {'name': 'Document', 'color': 'blue'},
                    {'name': 'Code', 'color': 'green'},
                    {'name': 'Research', 'color': 'purple'},
                    {'name': 'Design', 'color': 'pink'},
                    {'name': 'Other', 'color': 'gray'}
                ]
            }
        },
        'Status': {
            'select': {
                'options': [
                    {'name': 'Draft', 'color': 'gray'},
                    {'name': 'In Review', 'color': 'yellow'},
                    {'name': 'Published', 'color': 'green'},
                    {'name': 'Archived', 'color': 'blue'}
                ]
            }
        },
        'Linear Ticket': {'url': {}},
        'Due Date': {'date': {}},
        'Completed Date': {'date': {}},
        'Description': {'rich_text': {}},
        'Tags': {'multi_select': {}}
    }


# =============================================================================
# SCHEMA REGISTRY
# =============================================================================

SCHEMAS = {
    'chores': chores_schema,
    'financials': financials_schema,
    'projects': projects_schema,
    'weekend-plans': weekend_plans_schema,
    'daily-briefing': daily_briefing_schema,
    'research': research_schema,
    'knowledge-base': knowledge_base_schema,
    'deliverables': deliverables_schema,
}


def get_schema(name: str) -> Dict[str, Any]:
    """Get schema by database name."""
    if name not in SCHEMAS:
        raise ValueError(f"Unknown schema: {name}. Available: {list(SCHEMAS.keys())}")
    return SCHEMAS[name]()


if __name__ == '__main__':
    import json
    print("Notion Database Schemas - SEM-94")
    print("=" * 50)
    for name, fn in SCHEMAS.items():
        print(f"\n{name}:")
        schema = fn()
        # Show first few properties
        props = list(schema.keys())[:5]
        print(f"  Properties: {', '.join(props)}")
        if len(schema) > 5:
            print(f"  ... and {len(schema) - 5} more")
    print("\n[OK] All schemas defined successfully")