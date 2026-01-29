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
    """Initialise les catégories et items du menu depuis le fichier JSON."""
    db = next(get_db())
    
    # Vérifier si des données existent déjà
    existing_categories = db.query(Category).count()
    if existing_categories > 0:
        print(f"✅ {existing_categories} catégories existent déjà. Skipping init...")
        return
    
    # Charger les données depuis le JSON
    data = load_menu_data()
    
    # Créer les catégories - mapper par ID JSON
    categories = {}  # json_id -> db_id
    category_names = {}  # json_id -> name (pour l'affichage)
    for cat_data in data["categories"]:
        json_id = cat_data.pop("id")  # Extraire l'ID JSON
        category = Category(**cat_data)
        db.add(category)
        db.flush()
        categories[json_id] = category.id
        category_names[json_id] = cat_data["name"]
    
    # Créer les menus
    item_count = 0
    for menu_data in data["menus"]:
        category_json_id = menu_data.pop("category")
        menu_data.pop("id", None)  # Retirer l'ID JSON (non stocké en DB)
        menu_item = MenuItem(
            category_id=categories[category_json_id],
            **menu_data
        )
        db.add(menu_item)
        item_count += 1
    
    # Créer les boissons
    for boisson_data in data["boissons"]:
        boisson_data.pop("id", None)  # Retirer l'ID JSON
        boisson = MenuItem(
            category_id=categories["cat_boissons"],
            item_type="boisson",
            **boisson_data
        )
        db.add(boisson)
        item_count += 1
    
    # Créer les extras
    for extra_data in data["extras"]:
        extra_data.pop("id", None)  # Retirer l'ID JSON
        extra = MenuItem(
            category_id=categories["cat_extra"],
            item_type="upsell",
            **extra_data
        )
        db.add(extra)
        item_count += 1
    
    db.commit()
    
    print(f"✅ Créé {len(data['categories'])} catégories")
    print(f"✅ Créé {item_count} items menu")
    print("\nCatégories:")
    for json_id, db_id in categories.items():
        count = db.query(MenuItem).filter(MenuItem.category_id == db_id).count()
        print(f"  - {json_id} (db_id={db_id}): {count} items")


if __name__ == "__main__":
    print("🔄 Initialisation des données menu...")
    init_menu_data()
    print("✅ Terminé!")
