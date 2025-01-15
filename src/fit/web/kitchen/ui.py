from datetime import datetime

import fasthtml.common as fh

from fit.web.common import DB


def create_add_items_modal():
    """Create the modal for adding kitchen items"""
    return fh.Div(
        fh.Dialog(
            fh.Div(
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
                            "Add Items Individually",
                            cls="btn btn-primary w-full mb-4",
                            onclick="/* Add individual items functionality will be added later */"
                        ),
                        fh.Button(
                            "Add Items in Bulk",
                            cls="btn btn-primary w-full",
                            onclick="/* Add bulk items functionality will be added later */"
                        ),
                        cls="space-y-4 mx-8"
                    ),
                    cls="p-6"
                ),
                cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg relative w-full"
            ),
            id="kitchen-modal",
            cls="modal"
        ),
        fh.Script("""
            function openKitchenModal() {
                document.getElementById('kitchen-modal').showModal();
            }
            
            function closeKitchenModal() {
                document.getElementById('kitchen-modal').close();
            }
        """)
    )


def create_fab():
    """Create the floating action button"""
    return fh.Button(
        "➕",
        cls="btn btn-circle btn-lg fixed bottom-8 right-8 text-2xl",
        onclick="openKitchenModal()"
    )


def create_expandable_section(title: str, content=None):
    """Create an expandable section with a title and optional content"""
    if content is None:
        content = fh.P("No items added yet", cls="text-primary-content text-center")

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


def create_kitchen_sections():
    """Create all kitchen inventory sections"""
    sections = [
        ("Produce", None),
        ("Meats & Fish", None),
        ("Dairy & Eggs", None),
        ("Bread & Grains", None),
        ("Frozen Items", None),
        ("Snacks & Misc", None)
    ]
    
    return fh.Div(
        *[create_expandable_section(title, content) for title, content in sections],
        cls="space-y-8"
    )


def kitchen_page_content():
    """Create the main kitchen page content"""
    content = fh.Article(
        fh.Div(
            fh.H2("Kitchen Inventory", cls="text-3xl font-bold text-primary-content mb-8"),
            create_kitchen_sections(),
            create_add_items_modal(),
            create_fab(),
            cls="max-w-6xl mx-auto p-6"
        ),
        cls="bg-base-100"
    )
    return content 