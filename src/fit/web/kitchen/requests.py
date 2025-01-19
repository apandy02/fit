import fit.web.common as common
import fit.web.kitchen.ui as ui


def get():
    """Return the kitchen inventory page content"""
    content = ui.kitchen_page_content()
    return common.page_outline(1, "Kitchen Inventory", content) 