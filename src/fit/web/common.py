import fasthtml.common as fh
import fh_bootstrap as fhb
from markdown import markdown

from fit.nutrition.assistants import Nutritionist, NutritionLogger
from fit.nutrition.targets import MICRO_GOALS
from fit.trackers.manager import get_active_tracker
from fit.web.databases import init_db

DB_PATH = "data/nutrition.db"
md_exts = ("codehilite", "smarty", "extra", "sane_lists", "md_in_html")

ALL_METRICS = [
    "calories",
    "protein",
    "carbs", 
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


DB = init_db(DB_PATH, ALL_METRICS, "default")
nutrition_logger = NutritionLogger()
active_tracker = get_active_tracker()
nutritionist = Nutritionist()
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
                    cls="flex items-center justify-end mb-2 opacity-0 transition-all duration-200 translate-y-[30px]",
                    id=f"{label.lower()}-button"
                )
                for label, emoji, onclick in buttons
            ],
            cls="absolute bottom-16 right-0 transition-all duration-200"
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
                {btn_id}Btn.style.opacity = '1';
                {btn_id}Btn.style.transform = 'translate(0, -{offset}px)';
            }} else {{
                {btn_id}Btn.style.opacity = '0';
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

def page_outline(selidx, title, *c):
    """
    Return the common page outline for the frontend.
    """
    return (
        fh.Title(title),
        fh.Body(
            fh.Html(data_theme="black"),
            fh.Div(
                fh.Div(
                    fh.A(
                        "Food",
                        href="/nutrition",
                        cls="btn btn-ghost text-white",
                    ),
                    fh.A(
                        "Progress",
                        href="/progress", 
                        cls="btn btn-ghost text-white",
                    ),
                    fh.A(
                        "Performance",
                        href="/performance",
                        cls="btn btn-ghost text-white",
                    ),
                    fh.A(
                        "Rest",
                        href="/rest",
                        cls="btn btn-ghost text-white",
                    ),
                    fh.A(
                        "Profile",
                        href="/profile",
                        cls="btn btn-ghost text-white",
                    ),
                    cls="flex justify-center items-center flex-1",
                ),
                cls="navbar bg-base-100 bg-opacity-100 rounded-m h-[5vh] flex justify-center outline outline-1 outline-primary-content",
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

# TODO: make it so that more parameters can be passed in to the function so it can be used to generate 
# more than just nutrition overviews
def create_overview_card(view_type: str):
    """Create the overview card with analysis button"""
    return fh.Card(
        fh.Div(
            fh.Div(
                fh.Button(
                    "Generate Daily Analysis" if view_type == "daily" else "Generate Weekly Analysis",
                    cls="btn btn-primary outline outline-1 outline-primary-content",
                    hx_post="/generate_daily_overview" if view_type == "daily" else "/generate_weekly_overview", # TODO create functions to analyze workout data
                    hx_target="#analysis-content"
                ),
                cls="flex justify-center mb-4"
            ),
            fh.Div(
                id="analysis-content",
                cls="prose max-w-none prose-invert"
            ),
            cls="p-6"
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
