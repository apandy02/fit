
import fasthtml.common as fh


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
            fh.H2("Your Kitchen", cls="text-3xl font-bold text-primary-content mb-8 text-center"),
            create_kitchen_sections(),
            cls="max-w-6xl mx-auto p-6"
        ),
        cls="bg-base-100"
    )
    return content 