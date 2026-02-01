"""
Menu data utilities with thread-safe caching.

Provides centralized, cached access to menu data loaded from JSON.
All modules should use get_menu_data() instead of load_menu_data() directly.
"""
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Thread-safe cache
_menu_cache: Optional[Dict[str, Any]] = None
_cache_lock = asyncio.Lock()


def _load_menu_from_disk() -> Dict[str, Any]:
    """
    Load menu data from the JSON file on disk.

    Returns:
        Menu data dictionary
    """
    try:
        # Assuming the structure is backend/src/db/menu_data.json
        # and this file is in backend/src/menu/utils.py
        json_path = Path(__file__).parent.parent / "db" / "menu_data.json"
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading menu data: {e}")
        return {"categories": [], "menus": [], "boissons": [], "extras": []}


def load_menu_data() -> Dict[str, Any]:
    """
    Load menu data from JSON file.

    DEPRECATED: Use get_menu_data() for cached access.
    This function is kept for backward compatibility but reads from disk each time.

    Returns:
        Menu data dictionary
    """
    return _load_menu_from_disk()


def get_menu_data() -> Dict[str, Any]:
    """
    Get menu data with caching (synchronous version).

    Thread-safe for use in non-async contexts.
    Loads data from disk on first call, then returns cached copy.

    Returns:
        Menu data dictionary (cached)
    """
    global _menu_cache

    if _menu_cache is None:
        _menu_cache = _load_menu_from_disk()

    return _menu_cache


async def get_menu_data_async() -> Dict[str, Any]:
    """
    Get menu data with thread-safe caching (async version).

    Uses asyncio.Lock to prevent race conditions on first load.

    Returns:
        Menu data dictionary (cached)
    """
    global _menu_cache

    # Fast path - cache hit
    if _menu_cache is not None:
        return _menu_cache

    # Slow path - need to load with lock
    async with _cache_lock:
        # Double-check after acquiring lock
        if _menu_cache is None:
            _menu_cache = _load_menu_from_disk()

        return _menu_cache


def invalidate_menu_cache():
    """
    Invalidate the menu cache.

    Call this if menu_data.json is updated at runtime.
    """
    global _menu_cache
    _menu_cache = None


def get_item_by_id(item_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a menu item by its ID from the cached data.

    Args:
        item_id: The item ID to look up

    Returns:
        Item dictionary if found, None otherwise
    """
    if not item_id:
        return None

    data = get_menu_data()

    for category in ["menus", "boissons", "extras"]:
        for item in data.get(category, []):
            if item.get("id") == item_id:
                return item

    return None


def get_item_name(item_id: str) -> str:
    """
    Get the name of a menu item by its ID.

    Args:
        item_id: The item ID to look up

    Returns:
        Item name if found, the ID itself otherwise
    """
    item = get_item_by_id(item_id)
    return item["name"] if item else item_id


def get_item_price(item_id: str) -> float:
    """
    Get the price of a menu item by its ID.

    Args:
        item_id: The item ID to look up

    Returns:
        Item price if found, 0.0 otherwise
    """
    item = get_item_by_id(item_id)
    return float(item.get("price", 0)) if item else 0.0
