from pydantic import BaseModel


class CategoryResponse(BaseModel):
    id: str
    title: str

    model_config = {"from_attributes": True}


class MenuItemResponse(BaseModel):
    id: int
    category_id: int
    title: str
    subtitle: str
    items: list[str] | None = None
    tag: str | None = None
    accent: str | None = None
    item_type: str
    price: str
    image: str | None = None
    remaining_quantity: int | None = None
    low_stock_threshold: int | None = None

    model_config = {"from_attributes": True}
