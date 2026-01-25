from pydantic import BaseModel
from typing import List, Optional

class OrderCombo(BaseModel):
    menu: Optional[str]
    boisson: Optional[str]
    bonus: Optional[str]
    quantity: int

class PrintSummaryResponse(BaseModel):
    start_time: str
    end_time: str
    combos: List[OrderCombo]
    total_orders: int
