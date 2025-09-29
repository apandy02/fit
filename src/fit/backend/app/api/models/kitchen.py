from typing import List

from pydantic import BaseModel, Field


class InventoryItem(BaseModel):
    title: str
    quantity: float
    unit: str
    category: str


class InventoryList(BaseModel):
    items: List[InventoryItem] = Field(default_factory=list)


class AddInventoryItemsRequest(BaseModel):
    items: List[InventoryItem]


class AddInventoryItemRequest(BaseModel):
    title: str
    quantity: float
    unit: str
    category: str


class InventoryFromTextRequest(BaseModel):
    items_description: str


class InstacartShoppingListLinkRequest(BaseModel):
    items: List[dict]


class InstacartShoppingListLinkResponse(BaseModel):
    link: str


class GroceryListItem(BaseModel):
    name: str
    quantity: float
    unit: str
    category: str
    value: str
    priority: int = Field(description="priority: low (0), medium (1), high (2)")


class GroceryList(BaseModel):
    overview: str
    items: List[GroceryListItem]
