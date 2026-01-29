from sqlalchemy import Boolean, Integer, String, Float, ForeignKey, Time, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from ..db.base import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    external_id: Mapped[str] = mapped_column(String, unique=True, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationship
    items: Mapped[list["MenuItem"]] = relationship("MenuItem", back_populates="category")


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    external_id: Mapped[str] = mapped_column(String, unique=True, nullable=True, index=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    tag: Mapped[str | None] = mapped_column(String, nullable=True)
    accent_color: Mapped[str | None] = mapped_column(String, nullable=True)
    item_type: Mapped[str] = mapped_column(String, nullable=False, default="menu")
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    low_stock_threshold: Mapped[int | None] = mapped_column(Integer, nullable=True)
    items: Mapped[list | None] = mapped_column(JSON, nullable=True)  # Liste des éléments du menu

    # Relationship
    # Relationship
    category: Mapped["Category"] = relationship("Category", back_populates="items")
    limits: Mapped[list["MenuItemLimit"]] = relationship("MenuItemLimit", back_populates="menu_item")

class MenuItemLimit(Base):
    __tablename__ = "menu_item_limits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    menu_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("menu_items.id"), nullable=False, index=True)
    
    start_time: Mapped[datetime] = mapped_column(Time, nullable=False) # e.g., 12:00
    end_time: Mapped[datetime] = mapped_column(Time, nullable=False)   # e.g., 13:00
    
    # Number allowed per hour in this interval. None = Infinite.
    max_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Current remaining quantity for this slot. None = Infinite.
    current_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)

    menu_item: Mapped["MenuItem"] = relationship("MenuItem", back_populates="limits")
