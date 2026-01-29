from fastapi import APIRouter, HTTPException
import json
from pathlib import Path
from typing import List

from .schemas import CategoryResponse, MenuItemResponse

router = APIRouter(tags=["menu"])

def load_menu_json():
    # Helper to load JSON data
    # Assuming the json is at src/db/menu_data.json relative to project root or similar
    # Adjust path as necessary. based on init_menu.py: src/db/menu_data.json
    try:
        json_path = Path(__file__).parent.parent / "db" / "menu_data.json"
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading menu data: {e}")
        return {"categories": [], "menus": [], "boissons": [], "extras": []}

@router.get("/categories", response_model=List[CategoryResponse])
def get_categories():
    """Get all active menu categories."""
    data = load_menu_json()
    
    categories = []
    for cat in data.get("categories", []):
        if cat.get("active", True):
            categories.append(CategoryResponse(
                id=cat["id"],
                title=cat["name"]
            ))
            
    # Sort by display_order if present, typically the list is already sorted or we can trust the list order
    return categories


@router.get("/items", response_model=List[MenuItemResponse])
def get_menu_items(category_id: str | None = None):
    """Get all available menu items, optionally filtered by category."""
    data = load_menu_json()
    all_items = []
    
    # Process Menus
    for item in data.get("menus", []):
        all_items.append({
            **item,
            "category_id": item["category"], # In JSON, menu links to category id
            "item_type": item.get("item_type", "menu")
        })
        
    # Process Boissons
    # Need to find beverage category ID
    beverage_cat_id = "cat_boissons" # Default assumption or find in categories
    # Or find it in categories list where name == "BOISSONS"
    
    # Let's rely on the IDs we put in the JSON
    # drink_coca -> category_id = "cat_boissons" 
    # But wait, in the JSON "boissons" list doesn't have "category" field explicit on each item usually? 
    # Let's check the JSON structure again.
    # The DB init script assigned them to "cat_boissons".
    # In JSON "boissons" are a top level list.
    
    for item in data.get("boissons", []):
        all_items.append({
            **item,
            "category_id": "cat_boissons", 
            "item_type": "boisson"
        })
        
    # Process Extras
    for item in data.get("extras", []):
        all_items.append({
            **item,
            "category_id": "cat_extra",
            "item_type": "upsell"
        })
    
    # Filtering
    if category_id:
        all_items = [i for i in all_items if i["category_id"] == category_id]
        
    # Mapping to response
    response = []
    for item in all_items:
        # Price formatting
        price_val = item.get("price", 0)
        formatted_price = f"{price_val:.2f} €".replace(".", ",")
        
        response.append(MenuItemResponse(
            id=item["id"],
            category_id=item["category_id"],
            title=item["name"],
            subtitle=item.get("description", "") or "",
            items=item.get("items"),
            tag=item.get("tag"),
            accent=item.get("accent_color"),
            item_type=item.get("item_type", "menu"),
            price=formatted_price,
            image=item.get("image_url"),
            remaining_quantity=None, # Infinite stock
            low_stock_threshold=None
        ))
        
    return response
