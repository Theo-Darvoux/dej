from pydantic import BaseModel


class CategoryResponse(BaseModel):
    id: str
    title: str

    model_config = {"from_attributes": True}


class MenuItemResponse(BaseModel):
    id: str
    category_id: str
    title: str
    subtitle: str
    items: list[str] | None = None
    allergens: dict[str, list[str]] | None = None
    tag: str | None = None
    accent: str | None = None
    item_type: str
    price: str
    image: str | None = None

    model_config = {"from_attributes": True}
