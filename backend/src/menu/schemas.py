from pydantic import BaseModel


class CategoryResponse(BaseModel):
    id: str
    title: str

    model_config = {"from_attributes": True}


class MenuItemResponse(BaseModel):
    title: str
    subtitle: str
    tag: str | None = None
    accent: str | None = None
    price: str

    model_config = {"from_attributes": True}
