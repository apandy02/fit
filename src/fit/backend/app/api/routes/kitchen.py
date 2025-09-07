import io
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image

from fit.backend.auth import get_current_user_id
from fit.backend.app.api.models.kitchen import (
    AddInventoryItemRequest,
    AddInventoryItemsRequest,
    GroceryList,
    InventoryFromTextRequest,
    InventoryItem,
    InventoryList,
)
from fit.ai.nutrition import assistants
from fit.backend.database.postgres_service import PostgresDatabaseService
from fit.backend.app.deps import get_database_service


router = APIRouter(tags=["kitchen"], prefix="/kitchen")


@router.get("/inventory", response_model=dict)
def get_inventory(user_id: int = Depends(get_current_user_id), database_service: PostgresDatabaseService = Depends(get_database_service)):
    return database_service.get_inventory(user_id)


@router.post("/inventory", status_code=201)
def add_inventory_item(req: AddInventoryItemRequest, user_id: int = Depends(get_current_user_id), database_service: PostgresDatabaseService = Depends(get_database_service)):
    try:
        database_service.insert_inventory_item(
            req.title, req.quantity, req.unit, req.category, user_id
        )
        return {"status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inventory/bulk", status_code=201)
def add_inventory_items(req: AddInventoryItemsRequest, user_id: int = Depends(get_current_user_id), database_service: PostgresDatabaseService = Depends(get_database_service)):
    try:
        for item in req.items:
            database_service.insert_inventory_item(
                item.title, item.quantity, item.unit, item.category, user_id
            )
        return {"status": "created", "count": len(req.items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/inventory/{rowid}", status_code=204)
def delete_inventory_item(rowid: int, user_id: int = Depends(get_current_user_id), database_service: PostgresDatabaseService = Depends(get_database_service)):
    ok = database_service.delete_inventory_item(rowid)
    if not ok:
        raise HTTPException(status_code=404, detail="Item not found")
    return None


@router.post("/inventory/from-text", response_model=InventoryList)
def add_inventory_from_text(req: InventoryFromTextRequest, user_id: int = Depends(get_current_user_id)):
    parsed = assistants.decipher_inventory(req.items_description).content[0].parsed
    # parsed is dm.KitchenInventory -> convert to API model
    items = [
        InventoryItem(title=i.name, quantity=i.quantity, unit=i.unit, category=i.category)
        for i in parsed.items
    ]
    return InventoryList(items=items)


@router.post("/inventory/from-image", response_model=InventoryList)
async def add_inventory_from_image(file: UploadFile = File(...), additional_context: Optional[str] = None, user_id: int = Depends(get_current_user_id)):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    parsed = assistants.inventory_from_image(image, additional_context or "").content[0].parsed
    items = [
        InventoryItem(title=i.name, quantity=i.quantity, unit=i.unit, category=i.category)
        for i in parsed.items
    ]
    return InventoryList(items=items)


@router.post("/grocery-list", response_model=GroceryList)
def generate_grocery_list(user_id: int = Depends(get_current_user_id), database_service: PostgresDatabaseService = Depends(get_database_service)):
    current_inventory = database_service.get_inventory(user_id)
    user_meals = database_service.get_all_meal_summaries(user_id)
    user_preferences = assistants.summarize_user_preferences(user_meals)
    dietary_restrictions = database_service.get_dietary_restrictions(user_id)
    result = assistants.generate_grocery_list(
        user_preferences, current_inventory, dietary_restrictions
    ).content[0].parsed
    return result


