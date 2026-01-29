"""
Script pour initialiser les données du menu depuis un fichier JSON.
Exécuter avec: python -m src.db.init_menu
"""

import json
from pathlib import Path
from sqlalchemy.orm import Session
from datetime import time
from src.db.session import get_db
from src.menu.models import Category, MenuItem, MenuItemLimit


def load_menu_data():
    """Charge les données du menu depuis le fichier JSON."""
    json_path = Path(__file__).parent / "menu_data.json"
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def init_menu_data():
    """Initialise ou met à jour les données du menu depuis le fichier JSON via external_id."""
    db = next(get_db())
    
    # Charger les données depuis le JSON
    data = load_menu_data()
    
    # 1. CATÉGORIES
    print("🔄 Syncing Categories...")
    categories_map = {}  # external_id -> db_obj
    
    for cat_data in data["categories"]:
        ext_id = cat_data.pop("id")
        name = cat_data["name"]
        
        # Chercher existant par ID ou Nom
        category = db.query(Category).filter((Category.external_id == ext_id) | (Category.name == name)).first()
        
        if category:
            # Update
            if not category.external_id:
                category.external_id = ext_id
                print(f"  🔗 Linked legacy category to id: {ext_id}")
            
            for key, value in cat_data.items():
                setattr(category, key, value)
            print(f"  📝 Updated category: {name}")
        else:
            # Create
            category = Category(external_id=ext_id, **cat_data)
            db.add(category)
            print(f"  ✨ Created category: {name}")
            
        db.flush()
        categories_map[ext_id] = category

    # 2. MENUS
    print("\n🔄 Syncing Menus...")
    for menu_data in data["menus"]:
        cat_ext_id = menu_data.pop("category")
        ext_id = menu_data.pop("id")
        name = menu_data["name"]
        
        category = categories_map.get(cat_ext_id)
        if not category:
            print(f"  ⚠️ Category {cat_ext_id} not found for menu {name}")
            continue

        menu_item = db.query(MenuItem).filter((MenuItem.external_id == ext_id) | (MenuItem.name == name)).first()
        
        menu_payload = {
            "category_id": category.id,
            **menu_data
        }

        if menu_item:
            if not menu_item.external_id:
                menu_item.external_id = ext_id
                print(f"  🔗 Linked legacy menu to id: {ext_id}")

            for key, value in menu_payload.items():
                setattr(menu_item, key, value)
            print(f"  📝 Updated menu: {name}")
        else:
            menu_item = MenuItem(external_id=ext_id, **menu_payload)
            db.add(menu_item)
            print(f"  ✨ Created menu: {name}")

    # 3. BOISSONS
    print("\n🔄 Syncing Drinks...")
    cat_boissons = categories_map.get("cat_boissons")
    for boisson_data in data["boissons"]:
        ext_id = boisson_data.pop("id")
        name = boisson_data["name"]
        
        boisson = db.query(MenuItem).filter((MenuItem.external_id == ext_id) | (MenuItem.name == name)).first()
        
        payload = {
            "category_id": cat_boissons.id,
            "item_type": "boisson",
            **boisson_data
        }

        if boisson:
            if not boisson.external_id:
                boisson.external_id = ext_id
                print(f"  🔗 Linked legacy drink to id: {ext_id}")
                
            for key, value in payload.items():
                setattr(boisson, key, value)
            print(f"  📝 Updated drink: {name}")
        else:
            boisson = MenuItem(external_id=ext_id, **payload)
            db.add(boisson)
            print(f"  ✨ Created drink: {name}")

    # 4. EXTRAS
    print("\n🔄 Syncing Extras...")
    cat_extra = categories_map.get("cat_extra")
    for extra_data in data["extras"]:
        ext_id = extra_data.pop("id")
        name = extra_data["name"]
        
        extra = db.query(MenuItem).filter((MenuItem.external_id == ext_id) | (MenuItem.name == name)).first()
        
        payload = {
            "category_id": cat_extra.id,
            "item_type": "upsell",
            **extra_data
        }

        if extra:
            if not extra.external_id:
                extra.external_id = ext_id
                print(f"  🔗 Linked legacy extra to id: {ext_id}")
                
            for key, value in payload.items():
                setattr(extra, key, value)
            print(f"  📝 Updated extra: {name}")
        else:
            extra = MenuItem(external_id=ext_id, **payload)
            db.add(extra)
            print(f"  ✨ Created extra: {name}")
    
    db.commit()
    print("\n✅ Database sync completed!")


if __name__ == "__main__":
    print("🔄 Initialisation des données menu...")
    init_menu_data()
    print("✅ Terminé!")
