import json
from pathlib import Path

def load_menu_data():
    """Load menu data from the JSON file."""
    try:
        # Assuming the structure is backend/src/db/menu_data.json
        # and this file is in backend/src/menu/utils.py
        json_path = Path(__file__).parent.parent / "db" / "menu_data.json"
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading menu data: {e}")
        return {"categories": [], "menus": [], "boissons": [], "extras": []}
