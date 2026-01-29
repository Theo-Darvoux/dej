from sqlalchemy import Column, Integer, String, Time, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from src.db.base import Base

class MenuItemLimit(Base):
    __tablename__ = "menu_item_limits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    item_id: Mapped[str] = mapped_column(String, nullable=False, index=True) # Matches JSON id (e.g. 'menu_boulanger')
    
    start_time: Mapped[datetime] = mapped_column(Time, nullable=False) # e.g., 12:00
    end_time: Mapped[datetime] = mapped_column(Time, nullable=False)   # e.g., 13:00
    
    # Number allowed per hour in this interval. None = Infinite.
    max_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Current remaining quantity for this slot. None = Infinite.
    current_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)