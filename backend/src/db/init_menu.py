"""
Script pour initialiser les données du menu.
Exécuter avec: python -m src.db.init_menu
"""

from sqlalchemy.orm import Session
from src.db.session import get_db
from src.menu.models import Category, MenuItem


def init_menu_data():
    """Initialise les catégories et items du menu une seule fois."""
    db = next(get_db())
    
    # Vérifier si des données existent déjà
    existing_categories = db.query(Category).count()
    if existing_categories > 0:
        print(f"✅ {existing_categories} catégories existent déjà. Skipping init...")
        return
    
    # Créer les catégories
    categories_data = [
        {"name": "Normal", "display_order": 1, "active": True},
        {"name": "Vegetarien", "display_order": 2, "active": True},
        {"name": "Sucre", "display_order": 3, "active": True},
        {"name": "Boissons", "display_order": 4, "active": False},
        {"name": "Upsell", "display_order": 5, "active": False},
    ]
    
    categories = {}
    for cat_data in categories_data:
        category = Category(**cat_data)
        db.add(category)
        db.flush()
        categories[cat_data["name"]] = category.id
    
    # Créer les items pour "Les offres"
    menu_items = [
        {
            "category_id": categories["Normal"],
            "name": "La base",
            "description": "Pizza + ",
            "price": 1,
            "tag": "Signature",
            "accent_color": "#f59e0b",
            "item_type": "menu",
            "display_order": 1,
        },
        {
            "category_id": categories["Vegetarien"],
            "name": "La base",
            "description": "Pizza + ",
            "price": 1,
            "tag": "Signature",
            "accent_color": "#84f50b",
            "item_type": "menu",
            "display_order": 2,
        },
        {
            "category_id": categories["Sucre"],
            "name": "La base",
            "description": "Brioche + truc",
            "price": 1,
            "tag": "Signature",
            "accent_color": "#0b59f5",
            "item_type": "menu",
            "display_order": 3,
        },
        {
            "category_id": categories["Boissons"],
            "name": "Boisson fraîche",
            "description": "Soda, eau ou jus",
            "price": 0,
            "tag": "Boisson",
            "accent_color": "#0bc6f5",
            "item_type": "boisson",
            "display_order": 4,
        },
        {
            "category_id": categories["Boissons"],
            "name": "Café / Thé",
            "description": "Boisson chaude",
            "price": 0,
            "tag": "Boisson",
            "accent_color": "#0bc6f5",
            "item_type": "boisson",
            "display_order": 5,
        },
        {
            "category_id": categories["Upsell"],
            "name": "Poulet grillé",
            "description": "Option poulet pour clients éligibles",
            "price": 0,
            "tag": "Option",
            "accent_color": "#9b5de5",
            "item_type": "upsell",
            "display_order": 6,
        },
    ]
    
    for item_data in menu_items:
        menu_item = MenuItem(**item_data)
        db.add(menu_item)
    
    db.commit()
    
    print(f"✅ Créé {len(categories_data)} catégories")
    print(f"✅ Créé {len(menu_items)} items menu")
    print("\nCatégories:")
    for cat_name, cat_id in categories.items():
        count = db.query(MenuItem).filter(MenuItem.category_id == cat_id).count()
        print(f"  - {cat_name} (id={cat_id}): {count} items")


if __name__ == "__main__":
    print("🔄 Initialisation des données menu...")
    init_menu_data()
    print("✅ Terminé!")
