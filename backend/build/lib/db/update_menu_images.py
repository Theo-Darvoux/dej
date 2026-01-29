
from sqlalchemy.orm import Session
from src.db.session import get_db
from src.menu.models import MenuItem

def update_menu_images():
    db = next(get_db())
    
    # List of available images from frontend/public/images
    # (Prepending /images/ for the frontend)
    images = [
        "/images/WhatsApp Image 2026-01-13 at 03.04.52 (1).jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.04.52.jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.04.53 (1).jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.04.53.jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.04.54 (1).jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.04.54.jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.04.55 (1).jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.04.55.jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.04.56 (1).jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.04.56.jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.04.57 (1).jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.04.57.jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.04.58 (1).jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.04.58.jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.04.59 (1).jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.04.59.jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.05.00.jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.05.01 (1).jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.05.01 (2).jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.05.01.jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.05.02 (1).jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.05.02.jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.05.03.jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.05.04 (1).jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.05.04.jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.05.05 (1).jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.05.05.jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.05.06 (1).jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.05.06.jpeg",
        "/images/WhatsApp Image 2026-01-13 at 03.05.07.jpeg",
    ]
    
    items = db.query(MenuItem).all()
    
    for i, item in enumerate(items):
        # Use an image from the list (wrapping around if needed)
        # This is arbitrary but fixed per item name for now
        image_idx = i % len(images)
        item.image_url = images[image_idx]
        print(f"Assigning {images[image_idx]} to {item.name}")
    
    db.commit()
    print(f"✅ Finished updating {len(items)} items.")

if __name__ == "__main__":
    update_menu_images()
