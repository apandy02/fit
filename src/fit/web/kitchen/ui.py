from datetime import datetime

import fasthtml.common as fh

from fit.web.common import DB


def create_text_input_form(
    title: str,
    textarea_label: str,
    textarea_placeholder: str,
    submit_text: str,
    hx_post_url: str,
    rows: int = 3,
    hx_target: str = "#text-input",
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
            cls="flex justify-between items-center mb-8"
        ),
        fh.Form(
            hx_post=hx_post_url,
            hx_target=hx_target,
            cls="space-y-6 w-[90%] mx-auto"
        )(
            *extra_fields,
            fh.Div(
                fh.Label(textarea_label, cls="label text-lg text-primary-content mb-2"),
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
                cls="btn btn-primary w-full text-lg mt-4"
            )
        ),
        cls="w-[600px] mx-auto px-8 py-6"
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
                            textarea_placeholder="Example: 2 apples, 1 loaf of whole wheat bread, 8 oz block of cheddar cheese",
                            submit_text="Add Items",
                            hx_post_url="/analyze_kitchen_items",  # This endpoint will be implemented later
                            rows=3
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
                    cls="relative"
                ),
                cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg relative w-full"
            ),
            id="kitchen-modal",
            cls="modal"
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