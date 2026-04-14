#!/usr/bin/env python3
"""
Discord Webhook Server - Scout's endpoint for Discord messages.
Receives forwarded messages from gateway, processes them, returns responses.

This skill integrates with:
- LLM (Minimax) for conversational responses
- Linear ticket creation
- Web search (ddg/tavily)
- Calendar check
"""
import os
import sys
import json
import logging
import re
import requests
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Config paths
CONFIG_DIR = PROJECT_ROOT / "config"
SECRETS_PATH = CONFIG_DIR / "secrets.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

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


def call_llm(api_key, endpoint, model, messages, temperature=0.7):
    """Call Minimax LLM."""
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
    if choices:
        return choices[0].get("message", {}).get("content", "")
    return ""


def process_with_llm(content: str, llm_config: dict) -> str:
    """Process message with LLM for conversational response."""
    
    system_prompt = """You are Scout, a helpful AI assistant. You help users with:

1. **Creating Linear tickets** - When users want to track a task or request
2. **Web search** - When users want to find information online  
3. **Calendar** - When users ask about their schedule or upcoming events
4. **General conversation** - When users just want to chat

Be helpful, concise, and conversational. If a user asks for something you can help with, offer to do it using the appropriate command format.

Available commands you can suggest:
- `create ticket for <task>` - Create a Linear ticket
- `search for <topic>` - Search the web
- `calendar` - Check their calendar

If a message is just casual chat, respond naturally and be friendly."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": content}
    ]
    
    try:
        response = call_llm(
            api_key=llm_config["api_key"],
            endpoint=llm_config["endpoint"],
            model=llm_config["model"],
            messages=messages,
            temperature=0.7
        )
        return response if response else "I'm not sure how to help with that. Try `help` for available commands."
    except Exception as e:
        logger.error(f"LLM error: {e}")
        return "I'm having trouble thinking right now. Try `help` for available commands."


# =============================================================================
# Action Handlers
# =============================================================================

def handle_linear_create_ticket(entities: dict) -> str:
    """Handle Linear ticket creation."""
    # Import from discord-bot folder (has hyphen, use direct path)
    import importlib.util
    discord_bot_path = PROJECT_ROOT / "skills" / "discord-bot" / "check.py"
    spec = importlib.util.spec_from_file_location("discord_bot_check", discord_bot_path)
    discord_bot_check = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(discord_bot_check)
    create_linear_ticket = discord_bot_check.create_linear_ticket
    
    title = entities.get("title", "")
    description = entities.get("description", "")
    
    if not title:
        return "Usage: `create ticket for <your request>`\nExample: `create ticket for updating my resume`"
    
    if not description:
        description = f"Request: {title}"
    
    try:
        result = create_linear_ticket(
            title=title[:60],
            description=description,
            priority=entities.get("priority", 2)
        )
        
        if result.get("success"):
            return f"📋 Created ticket **{result['identifier']}**\n{result.get('url', '')}"
        else:
            return "❌ Failed to create ticket. Please try again."
    except Exception as e:
        logger.error(f"Ticket creation error: {e}")
        return f"❌ Error: {str(e)}"


def handle_web_search(entities: dict) -> str:
    """Handle web search."""
    query = entities.get("query", "")
    
    if not query:
        return "Usage: `search for <topic>`\nExample: `search for Python tutorials`"
    
    # Try tavily first
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "skills" / "openclaw-tavily-search"))
        from scripts.tavily_search import tavily_search
        
        results = tavily_search(
            query=query,
            max_results=5,
            include_answer=True,
            search_depth="basic"
        )
        
        if results:
            answer = results.get("answer", "")
            if answer:
                return f"🔍 **{query}**\n\n{answer[:1500]}"
            
            # Fall back to results list
            result_lines = []
            for r in results.get("results", [])[:3]:
                title = r.get("title", "Result")
                url = r.get("url", "")
                content = r.get("content", "")[:100]
                result_lines.append(f"• **{title}**\n  {content}...")
            
            if result_lines:
                return f"🔍 **{query}**\n\n" + "\n".join(result_lines)[:1500]
    except Exception as e:
        logger.warning(f"Tavily search failed: {e}")
    
    # Fallback: use duckduckgo via URL
    try:
        import urllib.request
        encoded_query = query.replace("+", "%2B").replace(" ", "+")
        url = f"https://lite.duckduckgo.com/lite/?q={encoded_query}"
        
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8", errors="replace")
        
        # Parse results from HTML (simplified)
        import re
        results = re.findall(r'<a class="result__a" href="([^"]+)">([^<]+)</a>', html)
        snippets = re.findall(r'<a class="result__snippet"[^>]*>([^<]+)</a>', html)
        
        if results:
            lines = [f"🔍 **{query}**"]
            for i, (url, title) in enumerate(results[:3]):
                snippet = snippets[i] if i < len(snippets) else ""
                lines.append(f"\n• **{title.strip()}**")
                if snippet:
                    lines.append(f"  {snippet.strip()[:100]}...")
            return "\n".join(lines)[:1500]
    except Exception as e:
        logger.error(f"DDG search error: {e}")
    
    return f"🔍 **{query}**\n\nSearch unavailable."


def handle_calendar_check(entities: dict) -> str:
    """Handle calendar check."""
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "skills" / "calendar-check"))
        from check import authenticate, fetch_events
        
        service = authenticate(readonly=True)
        if not service:
            return "📅 Calendar not configured. Run `python -m skills.calendar-check.auth` first."
        
        events = fetch_events(service, lookback_minutes=0, max_results=10)
        
        # Filter to only future events
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        future_events = []
        for event in events:
            start = event.get('start', '')
            if 'T' in start:
                try:
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    if start_dt > now:
                        future_events.append(event)
                except:
                    pass
        
        if not future_events:
            return "📅 No upcoming events."
        
        lines = ["📅 **Upcoming Events:**"]
        for event in future_events[:5]:
            start = event.get('start', '')
            if 'T' in start:
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                time_str = start_dt.strftime('%b %d at %I:%M %p')
            else:
                time_str = start
            lines.append(f"• **{event.get('title', 'Busy')}** - {time_str}")
        
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Calendar check error: {e}")
        return "📅 Calendar check unavailable."


def process_message(content: str, llm_config: dict) -> str:
    """Process message and return response."""
    
    # Check for direct commands first
    content_lower = content.lower().strip()
    
    if content_lower.startswith("create ticket"):
        # Extract request text
        request_text = content_lower.replace("create ticket", "").strip()
        if request_text.startswith("for "):
            request_text = request_text[4:]
        
        if not request_text:
            return "Usage: `create ticket for <your request>`\nExample: `create ticket for updating my resume`"
        
        return handle_linear_create_ticket({"title": request_text})
    
    elif content_lower.startswith("search for ") or content_lower.startswith("search "):
        query = content_lower.replace("search for ", "").replace("search ", "").strip()
        return handle_web_search({"query": query})
    
    elif content_lower.startswith("calendar") or "what's next" in content_lower or "my schedule" in content_lower:
        return handle_calendar_check({})
    
    elif content_lower in ["help", "hi", "hello"]:
        return """🤖 **Scout Commands**

• `create ticket for <request>` - Create a Linear ticket
• `search for <topic>` - Search the web
• `calendar` - Check upcoming events

Just type naturally and I'll help!"""
    
    else:
        # Use LLM for conversational response
        return process_with_llm(content, llm_config)


# =============================================================================
# HTTP Server
# =============================================================================

class WebhookHandler(BaseHTTPRequestHandler):
    """HTTP handler for Scout webhook."""
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "scout-discord-webhook"}).encode())
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle incoming Discord messages."""
        
        if self.path == "/discord/in":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            
            try:
                message_data = json.loads(body)
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
                return
            
            # Extract message content
            content = message_data.get("content", "")
            message_id = message_data.get("messageId", "")
            channel_id = message_data.get("channelId", "")
            
            logger.info(f"Processing message {message_id} from channel {channel_id}")
            
            # Get LLM config
            llm_config = get_llm_config()
            
            # Process message
            response_content = process_message(content, llm_config)
            response = {
                "content": response_content,
                "reply_to_message_id": message_id
            }
            
            # Send response
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        logger.info(format % args)


def main():
    port = 3001  # Different from gateway's 3000
    server = HTTPServer(("0.0.0.0", port), WebhookHandler)
    
    logger.info(f"Scout Discord Webhook starting on port {port}")
    logger.info(f"Endpoint: http://localhost:{port}/discord/in")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()