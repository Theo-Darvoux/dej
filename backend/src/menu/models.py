from sqlalchemy import Boolean, Integer, String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from ..db.base import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationship
    items: Mapped[list["MenuItem"]] = relationship("MenuItem", back_populates="category")


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    tag: Mapped[str | None] = mapped_column(String, nullable=True)
    accent_color: Mapped[str | None] = mapped_column(String, nullable=True)
    item_type: Mapped[str] = mapped_column(String, nullable=False, default="menu")
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationship
    category: Mapped["Category"] = relationship("Category", back_populates="items")
