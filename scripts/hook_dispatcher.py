#!/usr/bin/env python3
"""
Hook dispatcher for Discord commands
Called by hooks/discord-commands/handler.ts via subprocess
"""
import sys
import os
import json
import argparse

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

def handle_email_command(args):
    """Handle !email command"""
    from skills.email_alerts.check import execute
    result = execute()
    return result

def handle_calendar_command(args):
    """Handle !calendar command"""
    from skills.calendar_confirm.check import execute
    result = execute()
    return result

def handle_help_command(args):
    """Handle !help command"""
    return {
        "success": True,
        "response": "Available commands:\n!email - Check emails\n!calendar - Check upcoming meetings\n!help - Show this help"
    }

COMMAND_HANDLERS = {
    "email": handle_email_command,
    "calendar": handle_calendar_command,
    "help": handle_help_command,
}

def main():
    parser = argparse.ArgumentParser(description="Hook dispatcher")
    parser.add_argument("command", help="Command to execute")
    parser.add_argument("--args", default="[]", help="JSON array of arguments")
    
    args = parser.parse_args()
    
    handler = COMMAND_HANDLERS.get(args.command.lower())
    if not handler:
        result = {
            "success": False,
            "error": f"Unknown command: {args.command}"
        }
    else:
        try:
            result = handler(args)
            if not isinstance(result, dict):
                result = {"success": True, "response": str(result)}
        except Exception as e:
            result = {"success": False, "error": str(e)}
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()