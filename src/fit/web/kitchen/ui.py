import fasthtml.common as fh
from fit.nutrition.data_models import KitchenItem, KitchenInventory
from fit.web.common import create_text_form_input
from fit.web.kitchen.constants import INVENTORY_UNITS, INVENTORY_CATEGORIES


def kitchen_page_content(inventory: dict):
    """Create the main kitchen page content"""
    content = fh.Article(
        fh.Div(
            fh.H2("My Kitchen", cls="text-3xl font-bold text-primary-content mb-8 text-center"),
            create_kitchen_sections(inventory),
            create_add_items_modal(),
            create_fab(),
            cls="max-w-6xl mx-auto p-6"
        ),
        cls="bg-base-100"
    )
    return content 


def create_kitchen_sections(inventory: dict):
    """Create all kitchen inventory sections"""
    print(f"{inventory=}")
    sections = [
        ("Produce", inventory.get("Produce", [])),
        ("Meats & Fish", inventory.get("Meats & Fish", [])),
        ("Dairy & Eggs", inventory.get("Dairy & Eggs", [])),
        ("Bread & Grains", inventory.get("Bread & Grains", [])),
        ("Frozen Items", inventory.get("Frozen Items", [])),
        ("Snacks & Misc", inventory.get("Snacks & Misc", []))
    ]
    
    return fh.Div(
        *[create_expandable_section(title, content) for title, content in sections],
        cls="space-y-8"
    )

def create_fab():
    """Create the floating action button"""
    return fh.Button(
        "➕",
        cls="btn btn-circle btn-lg fixed bottom-8 right-8 text-2xl",
        onclick="openKitchenModal()"
    )


def create_expandable_section(title: str, items: list):
    """Create an expandable section with a title and optional content"""
    if len(items) == 0:
        content = fh.P("No items added yet", cls="text-primary-content text-center")
    else:
        content = fh.Div(
            *[create_item_card(item) for item in items],
            cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        )

    return fh.Div(
        fh.Details(
            fh.Summary(
                fh.H3(title, cls="text-xl font-bold text-primary-content inline-block"),
                cls="cursor-pointer hover:opacity-80"
            ),
            content,
            cls="p-6"
        ),
        cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg mt-8"
    )

def create_item_card(item: tuple):
    """Create a card for an item"""
    item['title'] = item['title'].capitalize()
    print(item)
    return fh.Card(
        fh.Button(
            "×",
            cls="absolute top-2 right-2 flex items-center justify-center h-8 w-8 hover:bg-base-300 focus:bg-base-300 rounded-lg bg-base-400 border-none outline-none text-primary-content text-xl font-light",
            hx_post=f"/delete_inventory_item/{item['rowid']}",
            hx_target="closest .card",
            hx_swap="outerHTML"
        ),
        fh.Div(
            fh.H2(item['title'], cls="card-title justify-center text-lg mb-2 text-primary-content"),
            fh.P(f"Quantity: {item['quantity']} {item['unit']}", cls="text-center text-primary-content text-sm"),
            fh.Div(
                fh.Button("Edit", cls="px-4 py-2 bg-base-200 hover:bg-base-100 rounded-lg text-primary-content text-sm outline outline-1 outline-primary-content"),
                cls="card-actions justify-center mt-3"
            ),
            cls="card-body items-center text-center py-4 px-4"
        ),
        cls="card bg-base-300 shadow-xl rounded-xl outline outline-1 outline-primary-content mt-4 max-w-[250px] relative"
    )


def create_text_input_form(
    title: str,
    textarea_label: str,
    textarea_placeholder: str,
    submit_text: str,
    hx_post_url: str,
    rows: int = 3,
    hx_target: str = "#describe-view",
    extra_fields: list = None,
    header_buttons: list = None
):
    """Create a reusable form for text input"""
    if extra_fields is None:
        extra_fields = []
    if header_buttons is None:
        header_buttons = []

    return fh.Div(
        fh.Div(
            fh.H3(title, cls="text-2xl font-bold text-primary-content inline-block"),
            *header_buttons,
            cls="flex justify-between items-center mb-4"
        ),
        fh.Form(
            hx_post=hx_post_url,
            hx_target=hx_target,
            hx_swap="outerHTML",
            cls="space-y-4 w-[90%] mx-auto"
        )(
            fh.Div(
                fh.Label(textarea_label, cls="label text-lg text-primary-content mb-1"),
                fh.Textarea(
                    name="items_description",
                    placeholder=textarea_placeholder,
                    rows=rows,
                    cls="textarea textarea-bordered w-full bg-base-200 text-primary-content text-lg"
                ),
                cls="form-control"
            ),
            fh.Button(
                submit_text,
                type="submit",
                cls="btn btn-primary w-full text-lg mt-2"
            )
        ),
        cls="w-full mx-auto px-4 py-2"
    )


def create_image_upload_form():
    """Create a form for uploading images of kitchen items"""
    return fh.Div(
        fh.H3("Upload Image", cls="text-2xl font-bold text-primary-content mb-8"),
        fh.Form(
            hx_post="/analyze_kitchen_image",  # This endpoint will be implemented later
            hx_target="#image-input",
            hx_encoding="multipart/form-data",
            cls="space-y-6 w-[90%] mx-auto"
        )(
            fh.Div(
                fh.Label("Upload a photo of your kitchen items", cls="label text-lg text-primary-content mb-2"),
                fh.Input(
                    type="file",
                    name="kitchen_image",
                    accept="image/*",
                    required=True,
                    cls="file-input file-input-bordered w-full bg-base-200 text-primary-content text-lg"
                ),
                cls="form-control"
            ),
            fh.Div(
                fh.Label("Additional Context (optional)", cls="label text-lg text-primary-content mb-2"),
                fh.Textarea(
                    name="additional_context",
                    placeholder="Add any additional details about the items in the image (e.g., quantities, brands)",
                    rows=2,
                    cls="textarea textarea-bordered w-full bg-base-200 text-primary-content text-lg"
                ),
                cls="form-control"
            ),
            fh.Button(
                "Analyze Image",
                type="submit",
                cls="btn btn-primary w-full text-lg mt-4"
            ),
            fh.Div(id="image-analysis-result")
        ),
        cls="w-[600px] mx-auto px-8 py-6"
    )


def create_add_items_modal():
    """Create the modal for adding kitchen items"""
    return fh.Div(
        fh.Dialog(
            fh.Div(
                fh.Div(
                    # Main View
                    fh.Div(
                        fh.Button(
                            "×",
                            cls="absolute right-4 top-4 text-xl font-light text-primary-content hover:text-primary-content focus:outline-none focus:ring-0 border-none outline-none",
                            onclick="closeKitchenModal()",
                            style="outline: none; box-shadow: none;"
                        ),
                        fh.H3("Add Items to Kitchen", cls="text-xl font-bold text-center mt-4 mb-8 text-primary-content"),
                        fh.Div(
                            fh.Button(
                                "Add Single Item",
                                cls="btn btn-primary w-full mb-4",
                                onclick="/* Add single item functionality will be added later */"
                            ),
                            fh.Button(
                                "Add Multiple Items",
                                cls="btn btn-primary w-full",
                                onclick="showBulkView()"
                            ),
                            cls="space-y-4 mx-8"
                        ),
                        cls="p-6",
                        id="main-view"
                    ),
                    # Bulk Items View
                    fh.Div(
                        fh.Button(
                            "←",
                            cls="absolute left-4 top-4 text-xl font-light text-primary-content hover:text-primary-content focus:outline-none focus:ring-0 border-none outline-none",
                            onclick="showMainView()",
                            style="outline: none; box-shadow: none;"
                        ),
                        fh.Button(
                            "×",
                            cls="absolute right-4 top-4 text-xl font-light text-primary-content hover:text-primary-content focus:outline-none focus:ring-0 border-none outline-none",
                            onclick="closeKitchenModal()",
                            style="outline: none; box-shadow: none;"
                        ),
                        fh.H3("Add Multiple Items", cls="text-xl font-bold text-center mt-4 mb-8 text-primary-content"),
                        fh.Div(
                            fh.Button(
                                "List Items",
                                cls="btn btn-primary w-full mb-4",
                                onclick="showDescribeView()"
                            ),
                            fh.Button(
                                "Upload a Picture",
                                cls="btn btn-primary w-full",
                                onclick="showImageView()"
                            ),
                            cls="space-y-4 mx-8"
                        ),
                        cls="p-6 hidden",
                        id="bulk-view"
                    ),
                    # Describe Items View
                    fh.Div(
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
                        create_text_input_form(
                            title="List Your Items",
                            textarea_label="Items List",
                            textarea_placeholder="Example: 2 apples, 1 loaf of whole wheat bread, 8 oz block of cheddar",
                            submit_text="Add Items",
                            hx_post_url="/decipher_text_inventory_addition",
                            rows=3,
                            hx_target="#describe-view"
                        ),
                        cls="p-6 hidden",
                        id="describe-view"
                    ),
                    # Image Upload View
                    fh.Div(
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
                        create_image_upload_form(),
                        cls="p-6 hidden",
                        id="image-view"
                    ),
                    cls="relative overflow-y-auto max-h-[80vh]"
                ),
                cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg relative w-full max-w-lg"
            ),
            id="kitchen-modal",
            cls="modal modal-middle"
        ),
        fh.Script("""
            function openKitchenModal() {
                document.getElementById('kitchen-modal').showModal();
                showMainView();
            }
            
            function closeKitchenModal() {
                document.getElementById('kitchen-modal').close();
            }

            function showMainView() {
                hideAllViews();
                document.getElementById('main-view').classList.remove('hidden');
            }

            function showBulkView() {
                hideAllViews();
                document.getElementById('bulk-view').classList.remove('hidden');
            }

            function showDescribeView() {
                hideAllViews();
                document.getElementById('describe-view').classList.remove('hidden');
            }

            function showImageView() {
                hideAllViews();
                document.getElementById('image-view').classList.remove('hidden');
            }

            function hideAllViews() {
                document.getElementById('main-view').classList.add('hidden');
                document.getElementById('bulk-view').classList.add('hidden');
                document.getElementById('describe-view').classList.add('hidden');
                document.getElementById('image-view').classList.add('hidden');
            }
        """)
    )

def create_editable_inventory_form(inventory: KitchenInventory):
    """Create a form for editing inventory items"""
    return fh.Div(
        fh.Form(
            hx_post="/save_inventory",
            hx_target="#save-result",
            id="inventory-form"
        )(
            fh.Div(
                fh.Div(
                    *[create_editable_inventory_card(inventory, index) for index, inventory in enumerate(inventory.items)],
                    cls="space-y-4",
                    id="inventory-items"
                ),
                fh.Button(
                    "Save Items",
                    type="submit",
                    cls="btn btn-primary w-full mt-4 ml-4"
                ),
                fh.Div(id="save-result", cls="mt-4"),
                cls="pr-8 space-y-4"
            )
        ),
        fh.Script("""
            function removeInventoryItem(index) {
                const itemElement = document.getElementById(`inventory-item-${index}`);
                if (itemElement) {
                    itemElement.remove();
                    
                    // If no items left, close modal and refresh
                    const itemsContainer = document.getElementById('inventory-items');
                    if (itemsContainer.children.length === 0) {
                        closeKitchenModal();
                        window.location.reload();
                    }
                }
            }
        """)
    )

def create_editable_inventory_card(inventory: KitchenItem, index: int):
    """Create a card for editing a single inventory item"""
    return fh.Card(
        fh.Button(
            "×",
            cls="absolute right-2 top-2 text-xl font-light text-primary-content hover:text-primary-content focus:outline-none focus:ring-0 border-none outline-none",
            onclick=f"removeInventoryItem({index})",
            style="outline: none; box-shadow: none;"
        ),
        fh.Div(
            create_item_form(inventory, index),
            cls="p-4"
        ),
        cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg shadow-none mt-4 w-full relative",
        id=f"inventory-item-{index}"
    )

def create_option_form_input(options: list, input_name: str, input_value: str):
    """Create a form input for a dropdown menu"""
    return fh.Select(
        *[fh.Option(option, value=option, selected=(option == input_value)) for option in options],
        cls="select select-bordered w-full max-w-xs",
        name=input_name
    )


def create_item_form(item: KitchenItem, index: int):
    """Create a form for editing a single inventory item"""
    return fh.Div(
        create_text_form_input(
            label_text="Item Name",
            input_name=f"items[{index}][title]",
            input_value=item.name,
            input_type="text"
        ),
        create_text_form_input(
            label_text="Quantity",
            input_name=f"items[{index}][quantity]",
            input_value=item.quantity,
            input_type="number",
            step="0.1"
        ),
        create_option_form_input(
            options=INVENTORY_UNITS,
            input_name=f"items[{index}][unit]",
            input_value=item.unit
        ),
        create_option_form_input(
            options=INVENTORY_CATEGORIES,
            input_name=f"items[{index}][category]",
            input_value=item.category
        ),
        cls="space-y-4",
        id="describe-view"
    )
