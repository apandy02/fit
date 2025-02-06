import fasthtml.common as fh
import fh_bootstrap as fhb
from markdown import markdown

from fit.nutrition.targets import MICRO_GOALS
from fit.web.databases import DatabaseService

DB_PATH = "data/nutrition.db"
md_exts = ("codehilite", "smarty", "extra", "sane_lists", "md_in_html")

ALL_METRICS = [
    "calories",
    "protein",
    "carbohydrates", 
    "fat",
    "fiber",
    "vitamin_a",
    "vitamin_c",
    "vitamin_d", 
    "calcium",
    "iron",
    "potassium",
    "sodium",
    "water",
    "creatine"
]


database_service = DatabaseService(DB_PATH)
micronutrient_goals = MICRO_GOALS["male"]


def create_fab_menu(buttons):
    """
    Create a floating action button menu with custom buttons.
    
    Args:
        buttons: List of tuples (label, emoji, onclick_handler)
    """
    return fh.Div(
        # Sub-buttons (initially hidden)
        fh.Div(
            *[
                fh.Div(
                    fh.Button(
                        fh.Span(emoji, cls="text-lg"),
                        cls="btn btn-primary btn-circle shadow-lg ml-3",
                        onclick=onclick
                    ),
                    cls="flex items-center justify-end mb-2",
                    id=f"{label.lower()}-button",
                    _hidden=True
                )
                for label, emoji, onclick in buttons
            ],
            cls="absolute bottom-16 right-0"
        ),
        # Main FAB
        fh.Button(
            fh.Span("+", cls="text-2xl transition-transform duration-200"),
            cls="btn btn-circle btn-outline",
            onclick=create_fab_animation_script([b[0].lower() for b in buttons])
        ),
        cls="fixed bottom-8 right-8"
    )

def create_fab_animation_script(button_ids):
    """Create the JavaScript for FAB button animations"""
    button_animations = []
    for i, btn_id in enumerate(button_ids):
        offset = 15 * (len(button_ids) - i)
        button_animations.append(f"""
            const {btn_id}Btn = document.getElementById('{btn_id}-button');
            if (this.classList.contains('btn-active')) {{
                {btn_id}Btn.hidden = false;
                {btn_id}Btn.style.transform = 'translate(0, -{offset}px)';
            }} else {{
                {btn_id}Btn.hidden = true;
                {btn_id}Btn.style.transform = 'translate(0, 15px)';
            }}
        """)
    
    return f"""
        this.classList.toggle('btn-active');
        this.firstElementChild.style.transform = this.classList.contains('btn-active') ? 'rotate(45deg)' : '';
        {' '.join(button_animations)}
    """

def create_modal(content, modal_id="modal"):
    """Create a modal with the given content"""
    return fh.Div(
        # Modal backdrop
        fh.Div(
            cls="fixed inset-0 bg-black bg-opacity-50 transition-opacity hidden",
            id=f"{modal_id}-backdrop",
            onclick=f"closeModal('{modal_id}')"
        ),
        fh.Div(
            fh.Div(
                fh.Button(
                    "×",
                    cls="absolute right-4 top-4 text-3xl font-light hover:text-gray-800 z-10",
                    onclick=f"closeModal('{modal_id}')"
                ),
                fh.Div(
                    content,
                    cls="space-y-6 overflow-y-auto max-h-[80vh] p-6"
                ),
                cls="bg-white rounded-lg shadow-xl relative w-full max-w-lg"
            ),
            cls="fixed inset-0 flex items-center justify-center p-4 hidden",
            id=modal_id
        ),
        fh.Script("""
            function openModal(id) {
                document.getElementById(id).classList.remove('hidden');
                document.getElementById(id + '-backdrop').classList.remove('hidden');
                document.body.style.overflow = 'hidden';
            }
            
            function closeModal(id) {
                document.getElementById(id).classList.add('hidden');
                document.getElementById(id + '-backdrop').classList.add('hidden');
                document.body.style.overflow = 'auto';
            }
        """)
    )

def page_outline(selidx, title, logged_in: bool, display_nav: bool, *c):
    """
    Return the common page outline for the frontend.
    """
    if display_nav:
        if logged_in:
            pages = [
                ("Food", "/nutrition"),
                ("Kitchen", "/kitchen"),
                ("Progress", "/progress"),
                ("Performance", "/performance"),
                ("Rest", "/rest"),
                ("Profile", "/profile"),
            ]
            justify = "center"
        else:
            pages = [
                ("Login", "/login"),
            ]
            justify = "right"
    else:
        pages = []
        justify = "center"
    return (
        fh.Title(title),
        fh.Body(
            fh.Html(data_theme="black"),
            fh.Div(
                fh.Div(
                    *[
                        fh.A(
                            title,
                            href=link,
                            cls="btn btn-ghost text-white",
                        )
                        for title, link in pages
                    ],
                    cls=f"flex justify-{justify} items-center flex-1",
                ),
                cls=f"navbar bg-base-100 bg-opacity-100 rounded-m h-[5vh] flex justify-{justify} outline outline-1 outline-primary-content",
            ),
            fh.Div(
                fh.Div(*c, cls="min-h-[calc(100vh-8vh)] pb-[3vh]"),
                cls="overflow-y-auto",
            ),
        ),
        
    )

def Markdown(s, exts=md_exts, **kw):
    """
    Enable markdown component rendering with left inner padding.
    """
    return fh.Div(fhb.NotStr(markdown(s, extensions=exts)), **kw)


def create_text_generation_card(endpoint: str, button_text: str = "Generate Analysis"):
    """Create the text generation card with analysis button"""
    
    return fh.Card(
        fh.Div(
            fh.Div(
                fh.Div(
                    fh.Button(
                        button_text,
                        cls="btn btn-primary outline outline-1 outline-primary-content mt-4 rounded-md",
                        hx_post=endpoint,
                        hx_target="#analysis-content",
                        hx_indicator="#loading-indicator"
                    ),
                    cls="flex justify-center"
                ),
                fh.Div(
                    fh.Span(
                        cls="loading loading-dots loading-md mt-4"
                    ),
                    id="loading-indicator",
                    cls="htmx-indicator flex justify-center"
                ),
            ),
            fh.Div(
                id="analysis-content",
                cls="prose max-w-none prose-invert"
            ),
            cls="px-6 py-4"
        ),
        cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg mb-12 text-primary-content"
    )


def create_time_filter(current_view: str):
    """Create the time filter toggle"""
    return fh.Div(
        fh.Select(
            fh.Option("Today", value="daily", selected=current_view == "daily"),
            fh.Option("This Week", value="weekly", selected=current_view == "weekly"),
            name="time_filter",
            cls="select select-bordered w-full max-w-xs",
            hx_post="/nutrition_redirect",
            hx_trigger="change",
        ),
        cls="mt-6 mb-8 flex justify-center"
    )

def create_text_form_input(label_text, input_name, input_value, input_type="number", step="0.1"):
    """Helper function to create a form input with label"""
    if input_type == "number":
        value = 0.0 if input_value is None or input_value == "" else float(input_value)
        formatted_value = "{:.1f}".format(value)
    else:
        formatted_value = input_value

    return fh.Div(
        fh.Label(label_text, cls="label text-primary-content"),
        fh.Input(
            type=input_type,
            name=input_name,
            value=formatted_value,
            step=step if input_type == "number" else None,
            cls="input input-bordered w-full bg-base-200 outline  text-primary-content"
        ),
        cls="form-control"
    )