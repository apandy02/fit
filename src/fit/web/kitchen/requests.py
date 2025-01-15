import fasthtml.common as fh

import fit.web.common as common
import fit.web.databases as db
import fit.web.kitchen.ui as ui
from fit.nutrition import assistants as assistants


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
        db.insert_inventory_item(item, quantity, unit, category)
        return fh.Response(status=200)
    except Exception as e:
        print(e)
        return fh.Response(status=500)


async def decipher_text_inventory_addition(request: fh.Request):
    """Analyze the text input for inventory addition"""
    try:
        form = await request.form()
        text = form.get("items_description")
        inventory = assistants.decipher_inventory(text).content[0].parsed
        for item in inventory.items:
            db.insert_inventory_item(common.DB, item.name, item.quantity, item.unit, item.category)
        
        return fh.Div(
            fh.P(
                "Items added successfully!",
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
            f"Error adding items: {str(e)}",
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