from datetime import datetime

import fasthtml.common as fh

from fit.nutrition.data import Goals, MealBreakdown
from fit.nutrition.targets import calculate_macro_targets
from fit.web.common import (DB, active_tracker, micronutrient_goals,
                            nutrition_logger, nutritionist, page_outline)
from fit.web.databases import (get_daily_cumulative_nutrition, get_daily_meals,
                               get_visible_metrics, insert_meal,
                               set_visible_metrics)
from fit.web.food_plots import create_plot


def metric_card(title: str, y_axis_title: str, plot_id: str, consumed: float, goal: float, burned: float = None, show_analysis: bool = True, allow_hide: bool = True):
    """Create a card containing a metric plot"""
    plot_data, plot_layout = create_plot(title, y_axis_title, consumed, goal, burned)
    
    analysis_text = None
    if show_analysis:
        macro_name = title.lower()
        if macro_name == "carbohydrates":
            macro_name = "carbohydrate"
        analysis_text = nutritionist.macro_analysis(macro_name, consumed, goal)
    
    # Add hide button if metric is hideable and not mandatory
    hide_button = None
    if allow_hide and title.lower() not in ["calories", "water", "creatine"]:
        hide_button = fh.Button(
            "×",
            cls="absolute right-2 top-2 text-xl font-light text-primary-content hover:text-primary-content focus:outline-none focus:ring-0 border-none outline-none",
            style="outline: none; box-shadow: none;",
            hx_post=f"/hide_metric/{plot_id}",
            hx_target=f"#{plot_id}-container",
            hx_swap="outerHTML"
        )
    
    return fh.Card(
        fh.Div(
            hide_button if hide_button else None,
            fh.Div(id=plot_id, cls="w-full h-full"),
            fh.Script(
                f"""
                Plotly.newPlot(
                    '{plot_id}',
                    {plot_data},
                    {plot_layout},
                    {{responsive: true}}
                );
                """
            ),
            fh.P(analysis_text, cls="text-sm text-primary-content mt-4") if analysis_text else None,
            cls="p-4 relative"  # Added relative positioning for absolute hide button
        ),
        cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg h-full text-primary-content",
        id=f"{plot_id}-container"
    )

def create_text_input_form(is_feedback: bool = False):
    """Create the text input form for meal description"""
    if not is_feedback:
        return fh.Card(
            fh.Div(
                fh.Header(
                    fh.H3("Describe Your Meal", cls="text-xl font-bold text-primary-content"),
                    cls="mb-6"
                ),
                fh.Form(
                    hx_post="/analyze_text",
                    hx_target="#text-input",
                    hx_swap="outerHTML",
                    cls="space-y-4"
                )(
                    fh.Div(
                        fh.Label("Meal Description", cls="label text-primary-content"),
                        fh.Textarea(
                            name="meal_description",
                            placeholder="Example: I had a grilled chicken sandwich with lettuce, tomato and mayo",
                            rows=3,
                            cls="textarea textarea-bordered w-full bg-base-200 outline  text-primary-content placeholder-slate-400"
                        ),
                        cls="form-control"
                    ),
                    fh.Button(
                        "Analyze Description",
                        type="submit",
                        cls="btn bg-primary"
                    )
                ),
                cls="p-6"
            ),
            cls="bg-base-200 rounded-lg"
        )
    else:
        return fh.Card(
            fh.Div(
                fh.Header(
                    fh.Div(
                        fh.H3("Refine Analysis", cls="text-xl font-bold text-primary-content"),
                        fh.Button(
                            "↺",
                            hx_post="/reset_text_form",
                            hx_target="#text-input",
                            cls="btn btn-ghost text-xl text-primary-content"
                        ),
                        cls="flex justify-between items-center"
                    ),
                    cls="mb-6"
                ),
                fh.Form(
                    hx_post="/regenerate_analysis",
                    hx_target="#text-result",
                    cls="space-y-4"
                )(
                    fh.Div(
                        fh.Label("Suggest Edits", cls="label text-primary-content"),
                        fh.Textarea(
                            name="feedback",
                            placeholder="Suggest edits to improve the analysis",
                            rows=2,
                            cls="textarea textarea-bordered w-full bg-base-200 outline  text-primary-content placeholder-slate-400"
                        ),
                        cls="form-control"
                    ),
                    fh.Input(
                        type="hidden",
                        name="original_description",
                        id="original_description"
                    ),
                    fh.Button(
                        "Regenerate",
                        type="submit",
                        cls="btn bg-primary"
                    ),
                    fh.Div(id="text-result", cls="mt-4")
                ),
                cls="p-6"
            ),
            cls="bg-base-200 rounded-lg"
        )

def create_image_upload_form():
    """Create the image upload form"""
    return fh.Card(
        fh.Div(
            fh.Header(
                fh.H3("Upload Food Image", cls="text-xl font-bold text-primary-content"),
                cls="mb-6"
            ),
            fh.Form(
                hx_post="/analyze_image",
                hx_target="#image-result",
                hx_encoding="multipart/form-data",
                cls="space-y-4"
            )(
                fh.Div(
                    fh.Label("Food Image", cls="label"),
                    fh.Input(
                        type="file",
                        name="food_image",
                        accept="image/*",
                        cls="file-input file-input-bordered w-full text-sm"
                    ),
                    cls="form-control"
                ),
                fh.Button(
                    "Upload & Analyze",
                    type="submit",
                    cls="btn btn-primary"
                ),
                fh.Div(id="image-result", cls="mt-4")
            ),
            cls="p-6"
        ),
        cls="bg-base-200 shadow-lg rounded-lg"
    )

def create_modal_content():
    """Create the content for the food tracking modal"""
    return fh.Div(
        # Close button
        fh.Button(
            "×",
            cls="absolute right-4 top-4 text-xl font-light text-primary-content hover:text-primary-content focus:outline-none focus:ring-0 focus:ring-offset-0 border-none outline-none z-10",
            onclick="closeModal()",
            style="outline: none; box-shadow: none;"
        ),
        # Back button (shown only when a form is visible)
        fh.Button(
            "←",
            cls="absolute left-4 top-4 text-xl font-light text-primary-content hover:text-primary-content focus:outline-none focus:ring-0 focus:ring-offset-0 border-none outline-none hidden z-10",
            onclick="showInputSelection()",
            style="outline: none; box-shadow: none;",
            id="back-button"
        ),
        # Initial selection view
        fh.Div(
            fh.Div(
                fh.H3("How would you like to log your meal?", cls="text-xl font-bold text-center mb-8 text-primary-content"),
                fh.Div(
                    # Image upload option
                    fh.Button(
                        fh.Div(
                            fh.Img(
                                src="/static/images/camera.png",
                                cls="h-12 w-auto object-contain mb-3"
                            ),
                            fh.P("Upload an image", cls="text-primary-content mb-2"),
                            cls="flex flex-col items-center justify-center h-full"
                        ),
                        cls="p-6 bg-base-200 bg-opacity-70 outline outline-1 outline-primary-content rounded-lg hover:bg-base-200 hover:bg-opacity-90 transition-colors w-full focus:outline-none mb-4 h-32",
                        onclick="showInputForm('image')"
                    ),
                    # Text description option
                    fh.Button(
                        fh.P("Describe it", cls="text-primary-content text-lg"),
                        cls="p-6 bg-base-200 bg-opacity-70 outline outline-1 outline-primary-content rounded-lg hover:bg-base-200 hover:bg-opacity-90 transition-colors w-full flex items-center justify-center focus:outline-none h-32",
                        onclick="showInputForm('text')"
                    ),
                    cls="flex flex-col space-y-4"
                ),
                id="input-selection",
                cls="p-6"
            ),
            # Hidden forms that will be shown when selected
            fh.Div(
                create_image_upload_form(),
                cls="hidden",
                id="image-input"
            ),
            fh.Div(
                create_text_input_form(),
                cls="hidden",
                id="text-input"
            ),
            cls="space-y-6 overflow-y-auto max-h-[80vh] bg-base-200 bg-opacity-70 rounded-lg relative w-full max-w-lg"
        ),
        cls="bg-transparent rounded-lg relative w-full max-w-lg"
    )

def food_tracking_modal():
    """Create the food tracking modal"""
    return fh.Div(
        fh.Div(
            cls="fixed inset-0 bg-slate-100 bg-opacity-25 transition-opacity hidden",
            id="modal-backdrop",
            onclick="closeModal()"
        ),
        fh.Div(
            create_modal_content(),
            cls="fixed inset-0 flex items-center justify-center p-4 hidden",
            id="food-modal"
        ),
        fh.Script("""
            function openFoodModal() {
                document.getElementById('food-modal').classList.remove('hidden');
                document.getElementById('modal-backdrop').classList.remove('hidden');
                document.body.style.overflow = 'hidden';
                document.getElementById('back-button').classList.add('hidden');
                showInputSelection();
            }
            
            function closeModal() {
                document.getElementById('food-modal').classList.add('hidden');
                document.getElementById('modal-backdrop').classList.add('hidden');
                document.body.style.overflow = 'auto';
                
                // Reset forms
                document.getElementById('text-result').innerHTML = '';
                document.querySelector('textarea[name="meal_description"]').value = '';
                document.getElementById('image-result').innerHTML = '';
                document.querySelector('input[type="file"]').value = '';
                
                // Hide back button
                document.getElementById('back-button').classList.add('hidden');
            }
            
            function showInputForm(type) {
                // Hide selection view
                document.getElementById('input-selection').classList.add('hidden');
                
                // Show selected input form
                if (type === 'image') {
                    document.getElementById('image-input').classList.remove('hidden');
                    document.getElementById('text-input').classList.add('hidden');
                } else {
                    document.getElementById('text-input').classList.remove('hidden');
                    document.getElementById('image-input').classList.add('hidden');
                }
                
                // Show back button
                document.getElementById('back-button').classList.remove('hidden');
            }
            
            function showInputSelection() {
                // Show selection view
                document.getElementById('input-selection').classList.remove('hidden');
                
                // Hide input forms
                document.getElementById('image-input').classList.add('hidden');
                document.getElementById('text-input').classList.add('hidden');
                
                // Hide back button
                document.getElementById('back-button').classList.add('hidden');
                
                // Reset forms
                document.getElementById('text-result').innerHTML = '';
                document.querySelector('textarea[name="meal_description"]').value = '';
                document.getElementById('image-result').innerHTML = '';
                document.querySelector('input[type="file"]').value = '';
            }
        """)
    )

def create_fab_menu():
    """Create the floating action button menu"""
    menu_items = [
        ("Food", "🍽️", "openFoodModal()"),
        ("Water", "💧", None)  # No handler yet
    ]
    
    return fh.Div(
        fh.Div(
            *[fh.Div(
                fh.Span(name, cls="text-primary-content text-sm font-medium"),
                fh.Button(
                    fh.Span(emoji, cls="text-lg"),
                    cls="btn btn-primary btn-circle ml-3",
                    onclick=handler if handler else None
                ),
                cls="flex items-center justify-end mb-2 opacity-0 transition-all duration-200 translate-y-[30px]",
                id=f"{name.lower()}-button"
            ) for name, emoji, handler in menu_items],
            cls="absolute bottom-16 right-0 transition-all duration-200"
        ),
        fh.Button(
            fh.Span("+", cls="text-2xl transition-transform duration-200"),
            cls="btn btn-primary btn-circle",
            onclick="""
                this.classList.toggle('btn-active');
                this.firstElementChild.style.transform = this.classList.contains('btn-active') ? 'rotate(45deg)' : '';
                
                const foodBtn = document.getElementById('food-button');
                const waterBtn = document.getElementById('water-button');
                
                if (this.classList.contains('btn-active')) {
                    foodBtn.style.opacity = '1';
                    waterBtn.style.opacity = '1';
                    foodBtn.style.transform = 'translate(0, -30px)';
                    waterBtn.style.transform = 'translate(0, -15px)';
                } else {
                    foodBtn.style.opacity = '0';
                    waterBtn.style.opacity = '0';
                    foodBtn.style.transform = 'translate(0, 15px)';
                    waterBtn.style.transform = 'translate(0, 15px)';
                }
            """
        ),
        cls="fixed bottom-8 right-8"
    )

def create_page_header():
    """Create the page header with title and time filter"""
    return fh.Div(
        fh.P("Nutritional Overview", cls="text-3xl font-bold text-center mb-6 text-primary-content"),
        fh.Div(
            fh.Select(
                fh.Option("Today", value="today", selected=True),
                fh.Option("This Week", value="week"),
                fh.Option("This Month", value="month"),
                name="time_filter",
                cls="select select-bordered w-full max-w-xs"
            ),
            cls="flex justify-center mb-8"
        ),
        cls="mb-8"
    )

def create_metric_overview_section(title, metrics_data, filtered_metrics, all_metrics=None):
    """Create a metrics overview section with configurable metrics"""
    metric_rows = [filtered_metrics[i:i+2] for i in range(0, len(filtered_metrics), 2)]
    
    # Create dropdown of hidden metrics if all_metrics is provided
    add_button = None
    if all_metrics:
        # Get metrics that are hidden (in all_metrics but not in filtered_metrics)
        hidden_metrics = [
            metric for metric in all_metrics 
            if metric["column_name"] not in [m["column_name"] for m in filtered_metrics]
        ]
        
        if hidden_metrics:
            dropdown_id = f"dropdown-{title.lower().replace(' ', '-')}"
            add_button = fh.Div(
                fh.Button(
                    "+",
                    cls="text-xl font-light text-primary-content hover:text-primary-content focus:outline-none focus:ring-0 border-none outline-none",
                    hx_get=f"/toggle_dropdown/{dropdown_id}",
                    hx_target=f"#{dropdown_id}",
                    hx_swap="innerHTML",
                    onclick=f"document.getElementById('{dropdown_id}').classList.toggle('hidden')"
                ),
                fh.Div(
                    cls="hidden absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-base-200 outline  ring-1 ring-black ring-opacity-5 z-10",
                    id=dropdown_id
                ),
                cls="relative inline-block text-left ml-2"
            )
    
    return fh.Section(
        fh.Div(
            fh.H3(f"{title}", cls="text-2xl font-bold text-center mb-8 text-primary-content"),
            add_button if add_button else None,
            cls="flex items-center justify-center"
        ),
        fh.Div(
            *[fh.Div(
                *[metric_card(
                    metric["name"],
                    f"{metric['name']} ({metric['unit']})" if metric["unit"] else metric["name"],
                    metric["plot_id"],
                    metrics_data[metric["column_name"]]["consumed"],
                    metrics_data[metric["column_name"]]["goal"],
                    metrics_data[metric["column_name"]].get("burned"),
                    allow_hide=metric["name"].lower() not in ["calories", "water", "creatine"]
                ) for metric in row],
                cls=f"{'w-1/2 mx-auto' if len(row) == 1 else 'grid grid-cols-2 gap-6'} mb-6"
            ) for row in metric_rows],
            cls="w-full"
        ),
        cls="w-full"
    )

def create_macro_section(data, visible_metrics):
    """Create the macronutrient metrics section"""
    macro_metrics = [
        {"name": "Calories", "column_name": "calories", "unit": "", "plot_id": "calories"},
        {"name": "Protein", "column_name": "protein", "unit": "g", "plot_id": "protein"},
        {"name": "Carbohydrates", "column_name": "carbs", "unit": "g", "plot_id": "carbs"},
        {"name": "Fat", "column_name": "fat", "unit": "g", "plot_id": "fat"}
    ]

    filtered_metrics = [
        metric for metric in macro_metrics 
        if metric["column_name"].lower() in visible_metrics
    ]

    return create_metric_overview_section("Macronutrients", data, filtered_metrics, macro_metrics)

def create_micro_section(data, visible_metrics):
    """Create the micronutrient metrics section"""
    micro_metrics = [
        {"name": "Vitamin A", "column_name": "vitamin_a", "unit": "IU", "plot_id": "vitamin_a"},
        {"name": "Vitamin C", "column_name": "vitamin_c", "unit": "mg", "plot_id": "vitamin_c"},
        {"name": "Iron", "column_name": "iron", "unit": "mg", "plot_id": "iron"},
        {"name": "Calcium", "column_name": "calcium", "unit": "mg", "plot_id": "calcium"}
    ]
    filtered_metrics = [
        metric for metric in micro_metrics 
        if metric["column_name"].lower() in visible_metrics
    ]
    return create_metric_overview_section("Micronutrients", data, filtered_metrics, micro_metrics)

def create_conditional_section(data, visible_metrics):
    """Create the conditionally essential nutrients section"""
    conditional_metrics = [
        {"name": "Creatine", "column_name": "creatine", "unit": "g", "plot_id": "creatine"}
    ]
    filtered_metrics = [
        metric for metric in conditional_metrics 
        if metric["column_name"].lower() in visible_metrics
    ]
    return create_metric_overview_section("Conditionally Essential Nutrients", data, filtered_metrics, conditional_metrics)

def create_water_section(data):
    """Create the water metrics section"""
    water_metrics = [
        {"name": "Water", "column_name": "water", "unit": "oz", "plot_id": "water-plot"}
    ]
    return create_metric_overview_section("Hydration", data, water_metrics)

def create_metrics_grid(data):
    """Create the grid of metric cards"""
    visible_metrics = get_visible_metrics(DB, "default") # TODO: get user_id from session, hardcoded for now

    sections = [
        create_overview_card(),
        create_macro_section(data, visible_metrics),
        create_micro_section(data, visible_metrics),
        create_conditional_section(data, visible_metrics),
        create_water_section(data)
    ]
    # Filter out None sections (those with all metrics hidden)
    sections = [section for section in sections if section is not None]
    
    return fh.Div(
        fh.Div(
            *sections,
            cls="w-full space-y-12"
        ),
        cls="w-full"
    )

def create_overview_card():
    """Create the overview card with analysis button"""
    return fh.Card(
        fh.Div(
            fh.Div(
                fh.Button(
                    "Generate Daily Analysis",
                    cls="btn btn-primary outline outline-1 outline-primary-content",
                    hx_post="/generate_overview",
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
        cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg mb-8 text-primary-content"
    )

async def generate_overview():
    """Generate the daily overview analysis"""
    today = datetime.date(datetime.today())
    meals = get_daily_meals(DB, today)

    calories_burned = active_tracker.get_daily_calories_burned(datetime.today())
    targets = calculate_macro_targets(calories_burned, Goals.MAINTAIN)
    targets.update(micronutrient_goals)
    analysis = nutritionist.daily_io_analysis(meals, targets)
    
    return fh.Card(
        fh.Div(
            *[
                fh.Div(
                    fh.P(fh.NotStr(line.strip()), cls="text-primary-content mb-1"),
                    cls="mb-2"
                )
                for line in analysis.split('\n')
                if line.strip() 
            ],
            cls="p-4 space-y-2 mt-2"
        ),
        cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg mt-4"
    )

def get():
    """Return the nutritional overview page content"""
    calories_burned = active_tracker.get_daily_calories_burned(datetime.today())
    goals = calculate_macro_targets(calories_burned, Goals.MAINTAIN) # goal hardcoded for now
    daily_consumption = get_daily_cumulative_nutrition(DB, datetime.date(datetime.today()))

    data = {
        "calories": {"consumed": daily_consumption.calories, "goal": goals["calories"], "burned": calories_burned},
        "protein": {"consumed": daily_consumption.protein, "goal": goals["protein"]},
        "carbs": {"consumed": daily_consumption.carbs, "goal": goals["carbs"]},
        "fat": {"consumed": daily_consumption.fat, "goal": goals["fat"]},
        "vitamin_a": {"consumed": daily_consumption.vitamin_a, "goal": micronutrient_goals["vitamin_a"]},
        "vitamin_c": {"consumed": daily_consumption.vitamin_c, "goal": micronutrient_goals["vitamin_c"]},
        "iron": {"consumed": daily_consumption.iron, "goal": micronutrient_goals["iron"]},
        "calcium": {"consumed": daily_consumption.calcium, "goal": micronutrient_goals["calcium"]},
        "water": {"consumed": 40, "goal": 64},
        "creatine": {"consumed": 2.0, "goal": 5.0}  # Added creatine with default values
    }

    content = fh.Article(
        fh.Div(
            create_page_header(),
            create_metrics_grid(data),
            food_tracking_modal(),
            create_fab_menu(),
            cls="max-w-6xl mx-auto p-6"
        ),
        cls="bg-base-100",
    )
    return page_outline(1, "Nutritional Overview", content)

def create_nutrition_section(title: str, items: list, cls: str = "mb-4"):
    """Create a section in the nutrition card"""
    return fh.Section(
        fh.H4(title, cls="font-medium mb-2"),
        fh.Ul(
            *[
                fh.Li(
                    fh.Span(f"{name}: ", cls="font-medium"),
                    value,
                    cls="mb-1"
                )
                for name, value in items
            ],
            cls="list-none"
        ),
        cls=cls
    )

def create_form_input(label_text, input_name, input_value, input_type="number", step="0.1"):
    """Helper function to create a form input with label"""
    # Ensure numeric values are formatted with one decimal place
    if input_type == "number":
        # Convert to float and handle None/empty values
        value = 0.0 if input_value is None or input_value == "" else float(input_value)
        # Format with one decimal place
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

def create_form_section(title, inputs, cls="mb-6"):
    """Helper function to create a form section with a title and inputs"""
    return fh.Section(
        fh.H4(title, cls="font-medium mb-4 text-primary-content"),
        fh.Div(
            *inputs,
            cls="grid grid-cols-2 gap-4"
        ),
        cls=cls
    )

def create_nutrition_card(nutrition_info):
    """Create a card containing ingredients text and editable nutrition form"""
    return fh.Card(
        fh.Div(
            fh.H4("Ingredients", cls="font-medium mb-2 text-primary-content"),
            fh.P(
                nutrition_info.ingredients,
                cls="mb-6 text-primary-content"
            ),
            # Add hidden fields for llm_summary and ingredients
            fh.Form(
                hx_post="/save_meal",
                hx_target="#save-result",
                cls="space-y-6"
            )(
                # Hidden fields
                fh.Input(
                    type="hidden",
                    name="summary",
                    value=nutrition_info.summary
                ),
                fh.Input(
                    type="hidden",
                    name="ingredients",
                    value=nutrition_info.ingredients
                ),
                # Nutrition inputs
                create_form_section("Nutrition Information", [
                    create_form_input("Meal Title", "summary", nutrition_info.summary, input_type="text"),
                    create_form_input("Calories (kcal)", "calories", nutrition_info.calories),
                    create_form_input("Protein (g)", "protein", nutrition_info.protein),
                    create_form_input("Carbs (g)", "carbs", nutrition_info.carbs),
                    create_form_input("Fat (g)", "fat", nutrition_info.fat),
                    create_form_input("Fiber (g)", "fiber", nutrition_info.fiber),
                    create_form_input("Vitamin A (IU)", "vitamin_a", nutrition_info.vitamin_a),
                    create_form_input("Vitamin C (mg)", "vitamin_c", nutrition_info.vitamin_c),
                    create_form_input("Vitamin D (IU)", "vitamin_d", nutrition_info.vitamin_d),
                    create_form_input("Calcium (mg)", "calcium", nutrition_info.calcium),
                    create_form_input("Iron (mg)", "iron", nutrition_info.iron),
                    create_form_input("Potassium (mg)", "potassium", nutrition_info.potassium),
                    create_form_input("Sodium (mg)", "sodium", nutrition_info.sodium),
                ]),
                fh.Button(
                    "Save Meal",
                    type="submit",
                    cls="btn btn-primary w-full"
                ),
                fh.Div(id="save-result", cls="mt-4")
            ),
            cls="space-y-4"
        ),
        cls="bg-base-200 outline  rounded-lg p-6"
    )

async def analyze_text(meal_description: str):
    """Handle meal description analysis"""
    nutrition_info = nutrition_logger.natural_language_macros(meal_description)
    return fh.Card(
        fh.Div(
            # Feedback form section
            fh.Div(
                fh.Header(
                    fh.Div(
                        fh.H3("Refine Analysis", cls="text-xl font-bold text-primary-content"),
                        fh.Button(
                            "↺",
                            hx_post="/reset_text_form",
                            hx_target="#text-input",
                            hx_swap="outerHTML",
                            cls="btn btn-ghost text-xl text-primary-content"
                        ),
                        cls="flex justify-between items-center"
                    ),
                    cls="mb-6"
                ),
                fh.Form(
                    hx_post="/regenerate_analysis",
                    hx_target="#nutrition-card",
                    cls="space-y-4"
                )(
                    fh.Div(
                        fh.Label("Suggest Edits", cls="label text-primary-content"),
                        fh.Textarea(
                            name="feedback",
                            placeholder="Suggest edits to improve the analysis",
                            rows=2,
                            cls="textarea textarea-bordered w-full bg-base-200 outline  text-primary-content placeholder-slate-400"
                        ),
                        cls="form-control"
                    ),
                    fh.Input(
                        type="hidden",
                        name="original_description",
                        id="original_description",
                        value=meal_description
                    ),
                    fh.Button(
                        "Regenerate",
                        type="submit",
                        cls="btn bg-primary"
                    )
                ),
                cls="mb-6"
            ),
            # Nutrition card section
            fh.Div(
                create_nutrition_card(nutrition_info),
                id="nutrition-card"
            ),
            cls="p-6"
        ),
        cls="bg-base-200 rounded-lg",
        id="text-input"  # Important: keep the same ID for proper replacement
    )

async def analyze_image(food_image: fh.UploadFile):
    """Handle image upload and analysis"""
    nutrition_info = nutrition_logger.image_macros(food_image)
    return create_nutrition_card(nutrition_info)

async def save_meal(request: fh.Request):
    """Save the meal with user-adjusted nutrition values"""
    try:
        form = await request.form()
        nutrition_info = MealBreakdown(
            summary=form["summary"],
            ingredients=form["ingredients"],
            calories=form["calories"],
            protein=form["protein"],
            carbs=form["carbs"],
            fat=form["fat"],
            fiber=form["fiber"],
            vitamin_a=form["vitamin_a"],
            vitamin_c=form["vitamin_c"],
            vitamin_d=form["vitamin_d"],
            calcium=form["calcium"],
            iron=form["iron"],
            potassium=form["potassium"],
            sodium=form["sodium"]
        )    
        insert_meal(DB, form["summary"], nutrition_info)
        
        return fh.Div(
            fh.P(
                "Meal saved successfully!",
                cls="text-green-500 font-semibold text-center mb-4"
            ),
            # Add script to reset the modal and reload page
            fh.Script("""
                // Show success message briefly
                setTimeout(() => {
                    // Reset text form
                    const textForm = document.querySelector('#text-result');
                    if (textForm) textForm.innerHTML = '';
                    const textArea = document.querySelector('textarea[name="meal_description"]');
                    if (textArea) textArea.value = '';
                    
                    // Reset image form
                    const imageForm = document.querySelector('#image-result');
                    if (imageForm) imageForm.innerHTML = '';
                    const fileInput = document.querySelector('input[type="file"]');
                    if (fileInput) fileInput.value = '';
                    
                    // Close the modal
                    closeModal();
                    
                    // Reload the page to show updated data
                    window.location.reload();
                }, 1000);
            """)
        )
    except Exception as e:
        return fh.P(
            f"Error saving meal: {str(e)}",
            cls="text-red-500 font-semibold text-center"
        )

async def reset_text_form():
    """Reset the text form to its original state"""
    return create_text_input_form(is_feedback=False)

async def regenerate_analysis(feedback: str, original_description: str):
    """Regenerate analysis based on feedback"""
    # First get the original nutrition info
    original_info = nutrition_logger.natural_language_macros(original_description)
    # Then improve it based on feedback
    improved_info = nutrition_logger.improve_breakdown(original_info, feedback)
    return create_nutrition_card(improved_info)

async def hide_metric(plot_id: str):
    """Hide a metric by removing it from visible_metrics"""
    visible_metrics = get_visible_metrics(DB, "default")

    if plot_id in visible_metrics:
        visible_metrics.remove(plot_id)
        set_visible_metrics(DB, visible_metrics, "default")
    return ""  # Return empty string to remove the card

async def show_metric(plot_id: str):
    """Show a previously hidden metric"""
    visible_metrics = get_visible_metrics(DB, "default")
    
    # Add the metric back to visible metrics
    # Extract the column name from plot_id by removing any suffixes
    column_name = plot_id.replace("-plot", "").replace("_", "")
    if column_name not in visible_metrics:
        visible_metrics.append(column_name)
        set_visible_metrics(DB, visible_metrics, "default")
    
    # Return the refreshed metrics grid
    return create_metrics_container(get_nutrition_data())

def get_nutrition_data():
    """Get the current nutrition data for display"""
    calories_burned = active_tracker.get_daily_calories_burned(datetime.today())
    goals = calculate_macro_targets(calories_burned, Goals.MAINTAIN)
    daily_consumption = get_daily_cumulative_nutrition(DB, datetime.date(datetime.today()))

    return {
        "calories": {"consumed": daily_consumption.calories, "goal": goals["calories"], "burned": calories_burned},
        "protein": {"consumed": daily_consumption.protein, "goal": goals["protein"]},
        "carbs": {"consumed": daily_consumption.carbs, "goal": goals["carbs"]},
        "fat": {"consumed": daily_consumption.fat, "goal": goals["fat"]},
        "vitamin_a": {"consumed": daily_consumption.vitamin_a, "goal": micronutrient_goals["vitamin_a"]},
        "vitamin_c": {"consumed": daily_consumption.vitamin_c, "goal": micronutrient_goals["vitamin_c"]},
        "iron": {"consumed": daily_consumption.iron, "goal": micronutrient_goals["iron"]},
        "calcium": {"consumed": daily_consumption.calcium, "goal": micronutrient_goals["calcium"]},
        "water": {"consumed": 40, "goal": 64},
        "creatine": {"consumed": 2.0, "goal": 5.0}
    }

def create_metrics_container(data):
    """Create the metrics grid with its container"""
    visible_metrics = get_visible_metrics(DB, "default")
    
    sections = [
        create_overview_card(),
        create_macro_section(data, visible_metrics),
        create_micro_section(data, visible_metrics),
        create_conditional_section(data, visible_metrics),
        create_water_section(data)
    ]
    # Filter out None sections (those with all metrics hidden)
    sections = [section for section in sections if section is not None]
    
    return fh.Div(
        fh.Div(
            *sections,
            cls="w-full space-y-12"
        ),
        cls="w-full",
        id="metrics-container"
    )

async def toggle_dropdown(dropdown_id: str):
    """Toggle the visibility of a dropdown"""
    visible_metrics = get_visible_metrics(DB, "default")
    
    # Get the appropriate metrics list based on the section
    if "macro" in dropdown_id:
        all_metrics = [
            {"name": "Calories", "column_name": "calories", "unit": "", "plot_id": "calories"},
            {"name": "Protein", "column_name": "protein", "unit": "g", "plot_id": "protein"},
            {"name": "Carbohydrates", "column_name": "carbs", "unit": "g", "plot_id": "carbs"},
            {"name": "Fat", "column_name": "fat", "unit": "g", "plot_id": "fat"}
        ]
    elif "micro" in dropdown_id:
        all_metrics = [
            {"name": "Vitamin A", "column_name": "vitamin_a", "unit": "IU", "plot_id": "vitamin_a"},
            {"name": "Vitamin C", "column_name": "vitamin_c", "unit": "mg", "plot_id": "vitamin_c"},
            {"name": "Iron", "column_name": "iron", "unit": "mg", "plot_id": "iron"},
            {"name": "Calcium", "column_name": "calcium", "unit": "mg", "plot_id": "calcium"}
        ]
    elif "conditional" in dropdown_id:
        all_metrics = [
            {"name": "Creatine", "column_name": "creatine", "unit": "g", "plot_id": "creatine"}
        ]
    else:
        return ""  # Return empty for unknown sections
    
    # Get hidden metrics
    hidden_metrics = [
        metric for metric in all_metrics 
        if metric["column_name"].lower() not in visible_metrics
    ]
    
    # Return the dropdown with its content
    return fh.Div(
        *[
            fh.A(
                metric["name"],
                cls="block w-full text-left px-4 py-2 text-sm text-primary-content hover:bg-base-200 outline  cursor-pointer",
                onclick=f"""
                    fetch('/show_metric/{metric["plot_id"]}', {{method: 'POST'}})
                        .then(response => response.text())
                        .then(html => {{
                            document.getElementById('metrics-container').outerHTML = html;
                            document.getElementById('{dropdown_id}').classList.add('hidden');
                        }});
                    return false;
                """,
                href="#"
            )
            for metric in hidden_metrics
        ],
        cls="absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-base-200 outline  ring-1 ring-black ring-opacity-5 z-10 block",  # Removed hidden class
        id=dropdown_id
    )
