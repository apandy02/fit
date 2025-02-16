import io
import logging

import fasthtml.common as fh
from PIL import Image

import fit.web.kitchen.ui as ui
from fit.nutrition import assistants as assistants
from fit.web.common import database_service, page_outline


def get(session):
    """Return the kitchen inventory page content"""
    inventory = get_inventory(session["user_id"])
    content = ui.kitchen_page_content(inventory)
    return page_outline(1, "Kitchen Inventory", True, True, content) 

async def add_item(session, request: fh.Request):
    """Add an item to the kitchen inventory"""
    try:
        form = await request.form()
        user_id = session["user_id"]
        item, quantity, unit, category = form.get("item"), form.get("quantity"), form.get("unit"), form.get("category")
        database_service.insert_inventory_item(item, quantity, unit, category, user_id)
        return fh.Response(status=200)
    except Exception as e:
        logging.error(f"Error adding item: {e}")
        return fh.Response(status=500)

async def add_inventory_from_image(food_image: fh.UploadFile, additional_context: str):
    """Add an inventory from an image"""
    try:
        contents = await food_image.read()
        image = Image.open(io.BytesIO(contents))
        inventory = assistants.inventory_from_image(image, additional_context)
        return ui.create_editable_inventory_form(inventory)
    except Exception:
        logging.e
        return fh.Response(status=500)

async def save_inventory(session, request: fh.Request):
    """Save the inventory items to the database"""
    try:
        form = await request.form()
        user_id = session["user_id"]
        items = []
        i = 0
        while f"items[{i}][title]" in form:
            items.append({
                "title": form[f"items[{i}][title]"],
                "quantity": float(form[f"items[{i}][quantity]"]),
                "unit": form[f"items[{i}][unit]"],
                "category": form[f"items[{i}][category]"]
            })
            i += 1
        
        for item in items:
            database_service.insert_inventory_item(
                item["title"],
                item["quantity"],
                item["unit"],
                item["category"],
                user_id
            )
        
        return fh.Div(
            fh.P(
                "Items saved successfully!",
                cls="text-green-500 font-semibold text-center"
            ),
            fh.Script("""
                setTimeout(() => {
                    closeKitchenModal();
                    window.location.reload();
                }, 1000);
            """)
        )
    except Exception as e:
        logging.e
        return fh.P(
            f"Error saving items: {str(e)}",
            cls="text-red-500 font-semibold text-center"
        )

def get_inventory(user_id: int):
    """Get the inventory from the database"""
    try:
        inventory = database_service.get_inventory(user_id)
        return inventory
    except Exception:
        logging.e
        return []
    
async def add_inventory_from_text(request: fh.Request):
    """Analyze the text input for inventory addition"""
    try:
        form = await request.form()
        text = form.get("items_description")
        inventory = assistants.decipher_inventory(text).content[0].parsed
        return ui.create_editable_inventory_form_modal(inventory)
    except Exception as e:
        logging.e
        return fh.P(
            f"Error analyzing items: {str(e)}",
            cls="text-red-500 font-semibold text-center"
        )

async def delete_inventory_item(rowid: int):
    """Delete an inventory item"""
    try:
        database_service.delete_inventory_item(rowid)
        return fh.Response(status=200)
    except Exception:
        logging.e
        return fh.Response(status=500)

async def generate_inventory_additions(session, request: fh.Request):
    """Generate inventory additions"""
    try:
        user_id = session["user_id"]
        current_inventory = get_inventory(user_id)
        user_meals = database_service.get_all_meal_summaries(user_id)
        user_preferences = assistants.summarize_user_preferences(user_meals)
        dietary_restrictions = database_service.get_dietary_restrictions(user_id)
        grocery_list = assistants.generate_grocery_list(
            current_inventory, user_preferences, dietary_restrictions
        ).content[0].parsed
        
        grocery_cards = []
        for item in grocery_list.items:
            grocery_cards.append(
                ui.grocery_suggestion_card(item)
            )
        
        return fh.Div(
            *grocery_cards,
            cls="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4"
        )
    except Exception:
        logging.e
        return fh.Response(status=500)