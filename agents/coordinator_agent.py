import os
import base64
import asyncio
import requests
from google import genai
from google.genai import types
from dotenv import load_dotenv
import sys
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

# Load the .env file containing GEMINI_API_KEY
load_dotenv()

# Initialize the Gemini client.
client = genai.Client()

# In-memory dictionary to store active chat sessions per user
user_chats = {}

async def execute_mcp_tool(category: str) -> str:
    """Executes the FastMCP server over stdio to fetch local rules using a robust synchronous subprocess wrapper."""
    def _run_mcp_sync():
        import subprocess
        import json
        
        proc = subprocess.Popen(
            [sys.executable, "-m", "mcp_server.server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "greenbin-client", "version": "1.0.0"}
            }
        }
        
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        tool_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "get_recycling_rules",
                "arguments": {"item_category": category}
            }
        }
        
        try:
            # Write init request
            proc.stdin.write(json.dumps(init_request) + "\n")
            proc.stdin.flush()
            
            # Read init response
            init_resp = json.loads(proc.stdout.readline())
            
            # Write initialized notification
            proc.stdin.write(json.dumps(initialized_notification) + "\n")
            proc.stdin.flush()
            
            # Write tool call request
            proc.stdin.write(json.dumps(tool_request) + "\n")
            proc.stdin.flush()
            
            # Read tool response
            tool_resp = json.loads(proc.stdout.readline())
            
            # Close connection
            proc.terminate()
            
            if "result" in tool_resp and "content" in tool_resp["result"]:
                content = tool_resp["result"]["content"]
                if content and len(content) > 0:
                    return content[0].get("text", "No rules found.")
            return "No rules found."
        except Exception as e:
            proc.terminate()
            import traceback
            traceback.print_exc()
            return "Unable to retrieve local rules."
            
    # Run the synchronous Popen loop in a separate thread to prevent blocking the async event loop
    return await asyncio.to_thread(_run_mcp_sync)

async def analyze_waste(user_query: str, image_url: str = None, user_id: str = "default") -> dict:
    """
    The main logic for the AI Coordinator.
    It takes user input, uses the Gemini model, and decides if it 
    needs to flag the item for human triage based on safety rules.
    """
    
    system_instruction = """
    You are the GreenBin Genius AI Coordinator.
    Your job is to classify waste items and determine if they are hazardous or difficult to recycle.
    ALWAYS use the 'get_recycling_rules' tool to fetch local municipal rules for the detected waste category before answering.
    If an item is clearly hazardous (e.g., batteries, oil, chemicals) or you are unsure, 
    you MUST return the exact phrase: 'NEEDS_REVIEW'.
    Otherwise, return 'SAFE' and provide the local disposal advice you fetched from the tool.
    """
    
    # Define the tool for Gemini
    mcp_tool = types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="get_recycling_rules",
                description="Get local municipal recycling and disposal rules for a specific category of item. Examples: 'batteries', 'plastics', 'cardboard', 'hazardous'. Call this BEFORE providing disposal advice.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "item_category": types.Schema(type="STRING")
                    },
                    required=["item_category"]
                )
            )
        ]
    )
    
    # Prepare the contents array
    contents_payload = [user_query]
    
    if image_url:
        try:
            if image_url.startswith("data:image"):
                header, encoded = image_url.split(",", 1)
                mime_type = header.split(":")[1].split(";")[0]
                image_bytes = base64.b64decode(encoded)
            elif image_url.startswith("http"):
                resp = requests.get(image_url, timeout=10)
                resp.raise_for_status()
                image_bytes = resp.content
                mime_type = resp.headers.get("Content-Type", "image/jpeg")
            else:
                image_bytes = None
                
            if image_bytes:
                image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                contents_payload.append(image_part)
        except Exception as e:
            print(f"Warning: Failed to decode or download image: {e}")

    try:
        # Fetch existing chat or create a new one to maintain conversational context
        if user_id not in user_chats:
            user_chats[user_id] = client.aio.chats.create(
                model='gemini-2.5-flash',
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                    tools=[mcp_tool]
                )
            )
        
        chat = user_chats[user_id]
        
        # Turn 1: Send user message
        response = await chat.send_message(contents_payload)
        
        # Check if Gemini requested a tool call
        if response.function_calls:
            for function_call in response.function_calls:
                if function_call.name == "get_recycling_rules":
                    category = function_call.args.get("item_category", "")
                    print(f"--> Agent requested MCP tool: get_recycling_rules('{category}')")
                    
                    # Execute MCP Server
                    tool_result = await execute_mcp_tool(category)
                    print(f"--> MCP Server returned: {tool_result}")
                    
                    # Turn 2: Send tool result back to Gemini
                    response = await chat.send_message(
                        types.Part.from_function_response(
                            name="get_recycling_rules",
                            response={"result": tool_result}
                        )
                    )
        
        agent_text = response.text
        
        # Security Feature: Human-in-the-loop fallback
        if agent_text.strip().startswith("NEEDS_REVIEW"):
            return {
                "status": "flagged",
                "notes": "Agent detected hazardous material or uncertainty. Triggering Human Review.",
                "raw_response": agent_text
            }
        else:
            clean_response = agent_text
            if clean_response.startswith("SAFE"):
                clean_response = clean_response[4:].strip()
                
            return {
                "status": "success",
                "notes": None,
                "raw_response": clean_response
            }
            
    except Exception as e:
        return {
            "status": "flagged",
            "notes": f"System error, defaulting to human review for safety. Error: {str(e)}",
            "raw_response": ""
        }
