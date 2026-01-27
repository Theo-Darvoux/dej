from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db.session import get_db
from .models import Category, MenuItem
from .schemas import CategoryResponse, MenuItemResponse

router = APIRouter(tags=["menu"])


@router.get("/categories", response_model=list[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """Get all active menu categories that have items with stock available."""
    from sqlalchemy import func, or_
    from .models import MenuItemLimit
    
    categories = db.query(Category).filter(Category.active == True).order_by(Category.display_order).all()
    
    if not categories:
        categories = db.query(Category).order_by(Category.display_order).all()
    
    # Filtrer les catégories qui ont au moins un item avec du stock
    result = []
    for cat in categories:
        # Récupérer tous les items de la catégorie
        items = db.query(MenuItem).filter(MenuItem.category_id == cat.id).all()
        
        has_stock = False
        for item in items:
            # Si l'item n'a pas de limites définies, il est considéré en stock infini
            if len(item.limits) == 0:
                has_stock = True
                break
            
            # Sinon, vérifier si au moins une limite a du stock
            for limit in item.limits:
                if limit.current_quantity is None or limit.current_quantity > 0:
                    has_stock = True
                    break
            
            if has_stock:
                break
        
        if has_stock:
            result.append(CategoryResponse(
                id=str(cat.id),
                title=cat.name
            ))
    
    return result


@router.get("/items", response_model=list[MenuItemResponse])
def get_menu_items(category_id: int | None = None, db: Session = Depends(get_db)):
    """Get all available menu items, optionally filtered by category."""
    query = db.query(MenuItem)
    
    if category_id:
        query = query.filter(MenuItem.category_id == category_id)
    
    items = query.order_by(MenuItem.display_order).all()
    
    response = []
    for item in items:
        # Calculate availability: Sum of current_quantity for all limits
        # None + anything = None (Infinity) logic
        remaining = None
        has_limits = len(item.limits) > 0
        
        if has_limits:
            total_remaining = 0
            is_infinite = False
            for limit in item.limits:
                if limit.current_quantity is None:
                    is_infinite = True
                    break
                total_remaining += limit.current_quantity
            
            if not is_infinite:
                remaining = total_remaining

        response.append(MenuItemResponse(
            title=item.name,
            subtitle=item.description or "",
            tag=item.tag,
            accent=item.accent_color,
            item_type=item.item_type,
            price=f"{item.price:.2f} €".replace(".", ","),
            image=item.image_url,
            remaining_quantity=remaining,
            low_stock_threshold=item.low_stock_threshold
        ))
        
    return response
