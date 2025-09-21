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


class GroceryListItem(BaseModel):
    name: str
    quantity: float
    unit: str
    category: str
    value: str


class GroceryList(BaseModel):
    items: List[GroceryListItem]
