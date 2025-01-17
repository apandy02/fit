import io

import fasthtml.common as fh
import fit.web.common as common
import fit.web.databases as db
import fit.web.kitchen.ui as ui
from fit.nutrition import assistants as assistants
from PIL import Image


def get():
    """Return the kitchen inventory page content"""
    inventory = get_inventory()
    print(inventory)
    content = ui.kitchen_page_content(inventory)
    return common.page_outline(1, "Kitchen Inventory", content) 

async def add_item(request: fh.Request):
    """Add an item to the kitchen inventory"""
    try:
        form = await request.form()
        item = form.get("item")
        quantity = form.get("quantity")
        unit = form.get("unit")
        category = form.get("category")
        db.insert_inventory_item(common.DB, item, quantity, unit, category)
        return fh.Response(status=200)
    except Exception as e:
        print(e)
        return fh.Response(status=500)

async def add_inventory_from_image(food_image: fh.UploadFile, additional_context: str):
    """Add an inventory from an image"""
    try:
        contents = await food_image.read()
        image = Image.open(io.BytesIO(contents))
        inventory = assistants.inventory_from_image(image, additional_context)
        return ui.create_editable_inventory_form(inventory)
    except Exception as e:
        print(e)
        return fh.Response(status=500)

async def save_inventory(request: fh.Request):
    """Save the inventory items to the database"""
    try:
        form = await request.form()
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
            db.insert_inventory_item(
                common.DB,
                item["title"],
                item["quantity"],
                item["unit"],
                item["category"]
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
        print(e)
        return fh.P(
            f"Error saving items: {str(e)}",
            cls="text-red-500 font-semibold text-center"
        )

def get_inventory():
    """Get the inventory from the database"""
    try:
        inventory = db.get_inventory(common.DB)
        return inventory
    except Exception as e:
        print(e)
        return []
    
async def add_inventory_from_text(request: fh.Request):
    """Analyze the text input for inventory addition"""
    try:
        form = await request.form()
        text = form.get("items_description")
        inventory = assistants.decipher_inventory(text).content[0].parsed
        return fh.Div(
            fh.Button(
                "←",
                cls="absolute left-4 top-4 text-xl font-light text-primary-content hover:text-primary-content focus:outline-none focus:ring-0 border-none outline-none",
                onclick="showBulkView()",
                style="outline: none; box-shadow: none;"
            ),
            fh.Button(
                "×",
                cls="absolute right-4 top-4 text-xl font-light text-primary-content hover:text-primary-content focus:outline-none focus:ring-0 border-none outline-none",
                onclick="closeKitchenModal()",
                style="outline: none; box-shadow: none;"
            ),
            fh.Div(
                ui.create_editable_inventory_form(inventory),
                cls="px-6"
            ),
            cls="p-6",
            id="describe-view"
        )
    except Exception as e:
        print(e)
        return fh.P(
            f"Error analyzing items: {str(e)}",
            cls="text-red-500 font-semibold text-center"
        )

async def delete_inventory_item(rowid: int):
    """Delete an inventory item"""
    try:
        common.DB.t.inventory.delete(rowid)
        # Return an empty div that will replace the card
        return fh.Div()
    except Exception as e:
        print(e)
        return fh.Response(status=500)