import json
import os
from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("GreenBin Municipal Rules")

def load_rules():
    db_path = os.path.join(os.path.dirname(__file__), "municipal_rules.json")
    try:
        with open(db_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

@mcp.tool()
def get_recycling_rules(item_category: str) -> str:
    """
    Get local municipal recycling and disposal rules for a specific category of item.
    Examples of item_category: 'batteries', 'plastics', 'cardboard', 'hazardous'
    """
    rules = load_rules()
    category_lower = item_category.lower()
    
    for key, rule in rules.items():
        if key in category_lower or category_lower in key:
            return rule
    
    return "No specific local rules found for this category. Please check with your local municipality or flag for human review."

if __name__ == "__main__":
    # Run the server
    mcp.run()
