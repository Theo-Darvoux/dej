import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from datetime import datetime, date, time, timedelta, timezone
from sqlalchemy.orm import Session
from src.db.session import get_db
from src.users.models import User
from src.menu.models import MenuItem
from src.reservations.schemas import BatimentMaisel

# Force addition of /app to sys.path for Docker
sys.path.append("/app")

def seed_fake_orders(count: int = 30):
    db = next(get_db())
    
    # Récupérer les items du menu par type
    menus = db.query(MenuItem).filter(MenuItem.item_type == "menu").all()
    boissons = db.query(MenuItem).filter(MenuItem.item_type == "boisson").all()
    bonus = db.query(MenuItem).filter(MenuItem.item_type == "upsell").all()
    
    if not menus:
        print("❌ Aucun menu trouvé. Veuillez d'abord initialiser le menu avec init_menu.py")
        return

    first_names = ["Léo", "Manon", "Hugo", "Emma", "Nathan", "Léa", "Enzo", "Chloé", "Louis", "Camille", "Théo", "Sarah", "Gabriel", "Jade", "Arthur"]
    last_names = ["Martin", "Bernard", "Thomas", "Petit", "Robert", "Richard", "Durand", "Dubois", "Moreau", "Laurent", "Simon", "Michel", "Lefebvre", "Leroy", "Roux"]
    
    # Date spécifique : 7 février 2026
    target_date = date(2026, 2, 7)
    # Créneaux horaires : piles (8h, 9h, ..., 21h)
    slots = [time(hour, 0) for hour in range(8, 22)]

    print(f"🔄 Génération de {count} commandes fictives pour le {target_date}...")

    for i in range(1, count + 1):
        email = f"dev_test_{i}_{random.randint(1000, 9999)}@example.com"
        
        # Vérifier si l'utilisateur existe déjà
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email, normalized_email=email.lower())
            db.add(user)
        
        user.prenom = random.choice(first_names)
        user.nom = random.choice(last_names)
        user.email_verified = True
        user.is_cotisant = random.choice([True, False])
        user.date_reservation = target_date
        user.heure_reservation = random.choice(slots)
        
        # Choix aléatoire des items
        user.menu_id = random.choice(menus).id
        user.boisson_id = random.choice(boissons).id if boissons and random.random() > 0.1 else None
        user.bonus_id = random.choice(bonus).id if bonus and random.random() > 0.3 else None
        
        user.habite_residence = random.choice([True, False])
        if user.habite_residence:
            user.adresse_if_maisel = random.choice(list(BatimentMaisel))
            user.numero_if_maisel = random.randint(100, 500)
            user.adresse = None
        else:
            user.adresse = f"{random.randint(1, 100)} Rue de l'Exemple, 91000 Évry"
            user.adresse_if_maisel = None
            user.numero_if_maisel = None
            
        user.phone = f"06{random.randint(10, 99)}{random.randint(10, 99)}{random.randint(10, 99)}{random.randint(10, 99)}"
        
        # Diversité des statuts de paiement
        payment_choice = random.random()
        if payment_choice < 0.7:
            user.payment_status = "completed"
            user.payment_date = datetime.now(timezone.utc)
            user.status = "confirmed"
        elif payment_choice < 0.9:
            user.payment_status = "pending"
            user.payment_date = None
            user.status = "pending"
        else:
            user.payment_status = "failed"
            user.payment_date = None
            user.status = "cancelled"
            
        user.last_ip = f"192.168.1.{random.randint(1, 254)}"
        user.total_amount = random.choice([5.0, 7.5, 10.0, 12.0])
        
    try:
        db.commit()
        print(f"✅ {count} commandes fictives créées avec succès !")
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors du seeding: {e}")

if __name__ == "__main__":
    import sys
    count = 30
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            pass
    seed_fake_orders(count)
