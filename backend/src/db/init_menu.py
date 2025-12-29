"""
Script pour initialiser les données du menu.
Exécuter avec: python -m src.db.init_menu
"""

from sqlalchemy.orm import Session
from src.db.session import get_db
from src.menu.models import Category, MenuItem


def init_menu_data():
    """Initialise les catégories et items du menu."""
    db = next(get_db())
    
    # Vérifier si des données existent déjà
    existing_categories = db.query(Category).count()
    if existing_categories > 0:
        print(f"❌ {existing_categories} catégories existent déjà. Suppression et réinit...")
        db.query(MenuItem).delete()
        db.query(Category).delete()
        db.commit()
    
    # Créer les catégories
    categories_data = [
        {"name": "Les offres", "display_order": 1},
        {"name": "En ce moment", "display_order": 2},
        {"name": "Spcecial Absinthe", "display_order": 3},
        {"name": "scpecial poulet", "display_order": 4},
    ]
    
    categories = {}
    for cat_data in categories_data:
        category = Category(**cat_data, active=True)
        db.add(category)
        db.flush()
        categories[cat_data["name"]] = category.id
    
    # Créer les items pour "Les offres"
    menu_items = [
        # Les offres
        {
            "category_id": categories["Les offres"],
            "name": "Menu Golden Ligue 1 McDonald's",
            "description": "Petit dej",
            "price": 12.90,
            "tag": "Signature",
            "accent_color": "#f59e0b",
            "display_order": 1,
        },
        {
            "category_id": categories["Les offres"],
            "name": "Menu Duo Golden Ligue 1 McDonald's",
            "description": "Petit dej",
            "price": 19.50,
            "tag": "Duo",
            "accent_color": "#6366f1",
            "display_order": 2,
        },
        
        # En ce moment
        {
            "category_id": categories["En ce moment"],
            "name": "Menu Golden Ligue 1 McDonald's",
            "description": "Petit dej",
            "price": 12.90,
            "tag": "En vedette",
            "accent_color": "#0ea5e9",
            "display_order": 1,
        },
        {
            "category_id": categories["En ce moment"],
            "name": "Menu Happy Doggy",
            "description": "Petit dej",
            "price": 9.40,
            "tag": "Nouveau",
            "accent_color": "#22c55e",
            "display_order": 2,
        },
        
        # Spcecial Absinthe
        {
            "category_id": categories["Spcecial Absinthe"],
            "name": "Spcecial Absinthe",
            "description": "Biere",
            "price": 6.00,
            "tag": "Edition limitée",
            "accent_color": "#16a34a",
            "display_order": 1,
        },
        {
            "category_id": categories["Spcecial Absinthe"],
            "name": "Absinthe Twist",
            "description": "Biere",
            "price": 6.50,
            "tag": "Mix",
            "accent_color": "#10b981",
            "display_order": 2,
        },
        
        # scpecial poulet
        {
            "category_id": categories["scpecial poulet"],
            "name": "scpecial poulet",
            "description": "Poulet",
            "price": 10.90,
            "tag": "Croustillant",
            "accent_color": "#ef4444",
            "display_order": 1,
        },
        {
            "category_id": categories["scpecial poulet"],
            "name": "Poulet Grillé",
            "description": "Poulet",
            "price": 9.90,
            "tag": "Grill",
            "accent_color": "#f97316",
            "display_order": 2,
        },
    ]
    
    for item_data in menu_items:
        menu_item = MenuItem(**item_data, available=True)
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
