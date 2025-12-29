from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db.session import get_db
from .models import Category, MenuItem
from .schemas import CategoryResponse, MenuItemResponse

router = APIRouter(prefix="/menu", tags=["menu"])


@router.get("/categories", response_model=list[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """Get all active menu categories."""
    categories = db.query(Category).filter(Category.active == True).order_by(Category.display_order).all()
    
    return [
        CategoryResponse(
            id=str(cat.id),
            title=cat.name
        )
        for cat in categories
    ]


@router.get("/items", response_model=list[MenuItemResponse])
def get_menu_items(category_id: int | None = None, db: Session = Depends(get_db)):
    """Get all available menu items, optionally filtered by category."""
    query = db.query(MenuItem).filter(MenuItem.available == True)
    
    if category_id:
        query = query.filter(MenuItem.category_id == category_id)
    
    items = query.order_by(MenuItem.display_order).all()
    
    return [
        MenuItemResponse(
            title=item.name,
            subtitle=item.description or "",
            tag=item.tag,
            accent=item.accent_color,
            price=f"{item.price:.2f} €".replace(".", ",")
        )
        for item in items
    ]
