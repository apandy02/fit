from datetime import datetime, timedelta

import fasthtml.common as fh
import fit.nutrition.assistants as assistants
import fit.web.nutrition.food_plots as food_plots
from fit.nutrition.data_models import MealBreakdown, NutritionFeedback
from fit.web.common import (create_text_form_input,
                            create_text_generation_card, create_time_filter,
                            database_service)


def metric_card(
        title: str,
        unit: str,
        y_axis_title: str,
        plot_id: str,
        data: list[tuple[float, float, float | None]],
        view_type: str = "daily"
    ):
    """Create a card containing a metric plot"""
    if view_type == "daily":
        plot_data, plot_layout, js_code = food_plots.create_apex_donut(data)
    else:
        plot_data, plot_layout, js_code = food_plots.create_plotly_bars(title, y_axis_title, data)
    
    consumed_values = []
    goal_values = []
    for i in range(len(data[0])):
        if data[0][i] is not None and data[1][i] is not None and data[1][i] > 0:
            consumed_values.append(data[0][i])
            goal_values.append(data[1][i])
    
    if consumed_values and goal_values:
        averages = sum(consumed_values) / len(consumed_values), sum(goal_values) / len(goal_values)
        analysis_text = assistants.nutrient_analysis(
            title, unit, averages[0], averages[1], multiple_days=view_type == "weekly"
        )
    else:
        analysis_text = None
    
    # Extract unit from y_axis_title if present
    unit = y_axis_title.split('(')[-1].strip(')') if '(' in y_axis_title else None
    display_title = f"{title} ({unit})" if unit else title
    
    # Create suggestions button separately to place at bottom
    suggestions_button = None
    if title.lower() != "water":
        suggestions_button = fh.Div(
            fh.Div(
                fh.Button(
                    "Get Suggestions",
                    cls="btn btn-sm btn-neutral outline outline-1 outline-base-content mt-4 rounded-md font-light text-xs",
                    hx_post=f"/get_nutrient_suggestions/{title.lower()}",
                    hx_target=f"#{plot_id}-suggestions",
                    hx_indicator=f"#{plot_id}-suggestions-loading-indicator"
                ),
                fh.Div(
                    fh.Span(
                        cls="loading loading-dots loading-md mt-2"
                    ),
                    id=f"{plot_id}-suggestions-loading-indicator",
                    cls="htmx-indicator"
                ),
                cls="flex flex-col items-center"
            ),
            cls="flex justify-center"
        )
    
    return fh.Card(
        fh.Div(
            fh.Div(
                fh.H3(display_title, cls="text-xl font-bold text-base-content text-center mt-4 mb-12"),
                fh.Div(id=plot_id, cls="w-full h-[300px]"),
                cls="w-full"
            ),
            fh.Div(
                fh.Script(js_code.replace("{plot_id}", plot_id)) if view_type == "daily" else
                fh.Script(
                    f"""
                    var data = {plot_data};
                    var layout = {plot_layout};
                    Plotly.newPlot('{plot_id}', data, layout, {{responsive: true}});
                    """
                ),
            ),
            fh.P(analysis_text, cls="text-md text-base-content mb-2 text-center") if analysis_text else None,
            fh.Div(
                suggestions_button,
                cls="flex justify-center"
            ) if suggestions_button else None,
            fh.Div(id=f"{plot_id}-suggestions"),
            cls="relative"
        ),
        cls="bg-base-200 outline outline-2 mx-4 my-2 outline-base-content rounded-2xl h-full text-base-content shadow-none",
        id=f"{plot_id}-container"
    )

def create_meal_prompt_form(
    title: str,
    textarea_label: str,
    textarea_placeholder: str,
    submit_text: str,
    hx_post_url: str,
    hx_target: str = "#text-input",
    extra_fields: list = None,
    header_buttons: list = None,
    rows: int = 3
):
    """Create a form for meal description or refinement input."""
    header_content = fh.H3(title, cls="text-xl font-bold text-base-content")
    if header_buttons:
        header_content = fh.Div(
            header_content,
            *header_buttons,
            cls="flex justify-between items-center"
        )
    
    return fh.Card(
        fh.Div(
            fh.Header(
                header_content,
                cls="mb-6"
            ),
            fh.Form(
                hx_post=hx_post_url,
                hx_target=hx_target,
                hx_swap="outerHTML",
                cls="space-y-4"
            )(
                fh.Div(
                    fh.Label(textarea_label, cls="label text-base-content"),
                    fh.Textarea(
                        name="meal_description" if "analyze" in hx_post_url else "feedback",
                        placeholder=textarea_placeholder,
                        rows=rows,
                        cls="textarea textarea-bordered w-full bg-base-200 outline text-base-content placeholder-slate-400"
                    ),
                    cls="form-control"
                ),
                fh.Div(
                    fh.Label("Meal Time", cls="label text-base-content"),
                    fh.Input(
                        type="time",
                        name="meal_time",
                        value=datetime.now().strftime("%H:%M"),
                        required=True,
                        cls="input input-bordered w-full bg-base-200 text-base-content"
                    ),
                    cls="form-control"
                ) if "analyze" in hx_post_url else None,
                *(extra_fields or []),
                fh.Button(
                    submit_text,
                    type="submit",
                    cls="btn btn-neutral w-1/2"
                )
            ),            
            cls="p-6"
        ),
        cls="bg-base-200 outline outline-1 outline-base-content rounded-lg mt-12 shadow-none "
    )

def create_text_input_form(is_feedback: bool = False, original_description: str = None, date: str | None = None, original_breakdown: MealBreakdown | None = None):
    """Create the text input form for meal description"""
    analyze_endpoint = f"/analyze_text/{date}" if date is not None else "/analyze_text"
    if not is_feedback:
        return create_meal_prompt_form(
            title="Describe Your Meal",
            textarea_label="Meal Description",
            textarea_placeholder="Example: I had a grilled chicken sandwich with lettuce, tomato and mayo",
            submit_text="Analyze Description",
            hx_post_url=analyze_endpoint,
            rows=3
        )
    else:
        return create_meal_prompt_form(
            title="Refine Analysis",
            textarea_label="Suggest Edits",
            textarea_placeholder="Suggest edits to improve the analysis",
            submit_text="Regenerate",
            hx_post_url="/regenerate_analysis",
            hx_target="#text-input",
            rows=2,
            extra_fields=[
                fh.Input(
                    type="hidden",
                    name="original_description",
                    id="original_description",
                    value=original_description
                ),
                # Add hidden fields for all the meal breakdown data
                fh.Input(
                    type="hidden",
                    name="original_breakdown",
                    id="original_breakdown",
                    value=original_breakdown.model_dump_json()
                )
            ],
            header_buttons=[
                fh.Button(
                    "↺",
                    hx_post="/reset_text_form",
                    hx_target="#text-input",
                    cls="btn btn-ghost text-xl text-base-content"
                )
            ]
        )

def create_image_upload_form():
    """Create the image upload form"""
    return fh.Card(
        fh.Div(
            fh.Header(
                fh.H3("Upload Food Image", cls="text-xl font-bold text-base-content"),
                cls="mb-6"
            ),
            fh.Form(
                hx_post="/analyze_image",
                hx_target="#image-input",
                hx_swap="outerHTML",
                hx_encoding="multipart/form-data",
                cls="space-y-4"
            )(
                fh.Div(
                    fh.Label("Food Image", cls="label text-base-content"),
                    fh.Input(
                        type="file",
                        name="food_image",
                        accept="image/*",
                        cls="file-input file-input-bordered w-full text-sm"
                    ),
                    cls="form-control"
                ),
                fh.Div(
                    fh.Label("Additional Context", cls="label text-base-content"),
                    fh.Textarea(
                        name="additional_context",
                        placeholder="Example: The sandwich in the image contains a fried chicken patty, not a grilled one",
                        cls="textarea textarea-bordered w-full bg-base-200 text-base-content"
                    ),
                    cls="form-control"
                ),
                fh.Div(
                    fh.Label("Meal Time", cls="label text-base-content"),
                    fh.Input(
                        type="time",
                        name="meal_time",
                        value=datetime.now().strftime("%H:%M"),
                        required=True,
                        cls="input input-bordered w-full bg-base-200 text-base-content"
                    ),
                    cls="form-control"
                ),
                fh.Button(
                    "Upload & Analyze",
                    type="submit",
                    cls="btn btn-neutral"
                )
            ),
            cls="p-6"
        ),
        cls="bg-base-200 shadow-lg rounded-lg"
    )

def create_modal_content(date: str | None = None):
    """Create the content for the food tracking modal"""
    return fh.Div(
        # Close button
        fh.Button(
            "×",
            cls="absolute right-4 top-4 text-xl font-light text-base-content hover:text-base-content focus:outline-none focus:ring-0 focus:ring-offset-0 border-none outline-none z-10",
            onclick="closeModal()",
            style="outline: none; box-shadow: none;"
        ),
        # Back button (shown only when a form is visible)
        fh.Button(
            "←",
            cls="absolute left-4 top-4 text-xl font-light text-base-content hover:text-base-content focus:outline-none focus:ring-0 focus:ring-offset-0 border-none outline-none hidden z-10",
            onclick="showInputSelection()",
            style="outline: none; box-shadow: none;",
            id="back-button"
        ),
        # Initial selection view
        fh.Div(
            fh.Div(
                fh.H3("How would you like to log your meal?", cls="text-xl font-bold text-center mb-8 text-base-content"),
                fh.Div(
                    # Image upload option
                    fh.Button(
                        "Upload an image",
                        cls="btn btn-neutral w-full justify-center text-lg font-light rounded-xl mb-4 outline outline-1 outline-primary-content",
                        onclick="showInputForm('image')"
                    ),
                    # Text description option
                    fh.Button(
                        "Describe it",
                        cls="btn btn-neutral w-full justify-center text-lg font-light rounded-xl mb-4 outline outline-1 outline-primary-content",
                        onclick="showInputForm('text')"
                    ),
                    cls="flex flex-col space-y-4 w-2/3 mx-auto"
                ),
                id="input-selection",
                cls="py-12 px-6"
            ),
            # Hidden forms that will be shown when selected
            fh.Div(
                create_image_upload_form(),
                cls="hidden",
                id="image-input"
            ),
            fh.Div(
                create_text_input_form(date=date),
                cls="hidden w-[90%] mx-auto",
                id="text-input"
            ),
            cls="space-y-6 overflow-y-auto max-h-[80vh] bg-base-200 bg-opacity-70 rounded-lg relative w-full max-w-lg"
        ),
        cls="bg-transparent rounded-lg relative w-full max-w-lg"
    )

def food_tracking_modal(date: str | None = None):
    """Create the food tracking modal"""
    return fh.Div(
        fh.Div(
            cls="fixed inset-0 bg-slate-500 bg-opacity-25 transition-opacity hidden",
            id="modal-backdrop",
            onclick="closeModal()"
        ),
        fh.Div(
            create_modal_content(date),
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

def water_tracking_modal(date: datetime | None = None):
    """Create the water tracking modal"""
    if date is None:
        date = datetime.today().date()
    log_water_endpoint = f"/log_water/{date.strftime('%Y-%m-%d')}"
    return fh.Div(
        fh.Dialog(
            fh.Div(
                fh.Div(
                    fh.Button(
                        "×",
                        cls="absolute right-4 top-4 text-xl font-light text-base-content hover:text-base-content focus:outline-none focus:ring-0 border-none outline-none",
                        onclick="closeWaterModal()",
                        style="outline: none; box-shadow: none;"
                    ),
                    fh.H3("Log Water", cls="text-xl font-bold text-center mt-4 mb-8 text-base-content"),
                    fh.Form(
                        hx_post=log_water_endpoint,
                        hx_target="#water-log-result",
                        cls="w-[90%] mx-auto space-y-6"
                    )(
                        fh.Div(
                            fh.Label("Amount (ml)", cls="label text-base-content"),
                            fh.Input(
                                type="number",
                                name="amount",
                                value="250",
                                step="50",
                                min="0",
                                required=True,
                                cls="input input-bordered w-full bg-base-200 text-base-content"
                            ),
                            cls="form-control"
                        ),
                        fh.Div(
                            fh.Label("Time", cls="label text-base-content"),
                            fh.Input(
                                type="time",
                                name="time_consumed",
                                value=datetime.now().strftime("%H:%M"),
                                required=True,
                                cls="input input-bordered w-full bg-base-200 text-base-content"
                            ),
                            cls="form-control"
                        ),
                        fh.Button(
                            "Log Water",
                            type="submit",
                            cls="btn btn-neutral w-full mt-6"
                        ),
                        fh.Div(id="water-log-result", cls="mt-4"),
                        cls="mx-8"
                    ),
                    cls="p-6"
                ),
                cls="bg-base-200 outline outline-1 outline-base-content rounded-lg relative w-full"
            ),
            id="water-modal",
            cls="modal"
        ),
        fh.Script("""
            function openWaterModal() {
                document.getElementById('water-modal').showModal();
            }
            
            function closeWaterModal() {
                document.getElementById('water-modal').close();
            }
        """)
    )

def create_page_header(current_view: str, date: datetime.date = None):
    """Create the page header with title and time filter"""
    today = datetime.today().date()
    
    # Create date navigation if we're in daily view
    date_nav = None
    if current_view == "daily" and date is not None:
        next_date = date + timedelta(days=1)
        prev_date = date - timedelta(days=1)
        
        date_nav = fh.Div(
            fh.A(
                "←",
                href=f"/nutrition/{prev_date.strftime('%Y-%m-%d')}",
                cls="text-xl font-light text-base-content hover:text-base-content"
            ),
            fh.P(
                date.strftime("%B %d, %Y"),
                cls="text-md font-light text-base-content mx-4"
            ),
            fh.A(
                "→",
                href=f"/nutrition/{next_date.strftime('%Y-%m-%d')}" if date < today else "#",
                cls=f"text-xl font-light {'text-base-content hover:text-base-content' if date < today else 'text-gray-400 cursor-not-allowed'}"
            ),
            cls="flex items-center justify-center mt-4"
        )
    
    return fh.Div(
        fh.H1("Nutrition Center", cls="text-4xl font-light text-center mb-2 text-base-content"),
        fh.P("Track your nutrition, get insights and suggestions", cls="text-md font-light text-base-content/60 text-center mb-4"),
        fh.Div(
            create_time_filter(current_view),
            cls="flex justify-center mb-6"
        ),
        date_nav if date_nav else None,
        supplement_modal(date),
        water_tracking_modal(date),
        cls="mb-8"
    )

def create_metric_overview_section(title, data, metrics, view_type: str = "daily"):
    """Create a metrics overview section with configurable metrics"""    
    return fh.Section(
        fh.Div(
            fh.H2(title, cls="text-3xl my-8 text-base-content text-center"),
            fh.Div(
                *[fh.Div(
                    metric_card(
                        metric["name"],
                        metric["unit"],
                        f"{metric['name']} ({metric['unit']})" if metric["unit"] else metric["name"],
                        metric["plot_id"],
                        (
                            data[metric["column_name"]]["consumed"],
                            data[metric["column_name"]]["goal"],
                            data[metric["column_name"]].get("burned")
                        ),
                        view_type=view_type
                    ),
                    cls="w-1/2 p-2" if i < len(metrics) - 1 or len(metrics) % 2 == 0 
                        else "w-1/2 p-2 mx-auto"
                ) for i, metric in enumerate(metrics)],
                cls="flex flex-wrap"
            ),
            cls="w-full"
        ),
        cls="w-full"
    )

def create_macro_section(data, view_type: str):
    """Create the macronutrient metrics section"""
    macro_metrics = [
        {"name": "Calories", "column_name": "calories", "unit": "", "plot_id": "calories"},
        {"name": "Protein", "column_name": "protein", "unit": "g", "plot_id": "protein"},
        {"name": "Carbohydrates", "column_name": "carbohydrates", "unit": "g", "plot_id": "carbohydrates"},
        {"name": "Fat", "column_name": "fat", "unit": "g", "plot_id": "fat"}
    ]
    return create_metric_overview_section("Macronutrients", data, macro_metrics, view_type)

def create_micro_section(data, view_type: str):
    """Create the micronutrient metrics section"""
    micro_metrics = [
        {"name": "Vitamin A", "column_name": "vitamin_a", "unit": "IU", "plot_id": "vitamin_a"},
        {"name": "Vitamin C", "column_name": "vitamin_c", "unit": "mg", "plot_id": "vitamin_c"},
        {"name": "Iron", "column_name": "iron", "unit": "mg", "plot_id": "iron"},
        {"name": "Calcium", "column_name": "calcium", "unit": "mg", "plot_id": "calcium"}
    ]
    return create_metric_overview_section("Micronutrients", data, micro_metrics, view_type)

def create_conditional_section(data, view_type: str):
    """Create the conditionally essential nutrients section"""
    conditional_metrics = [
        {"name": "Creatine", "column_name": "creatine", "unit": "g", "plot_id": "creatine"}
    ]
    return create_metric_overview_section("Conditionally Essential Nutrients", data, conditional_metrics, view_type)

def create_metrics_grid(user_id, data, water_metrics, view_type: str, date: datetime.date = None):
    """Create the grid of metric cards"""
    if view_type == "daily":
        text_generation_endpoint = "/generate_daily_nutrition_overview"
        if date is not None:
            text_generation_endpoint += f"/{date.strftime('%Y-%m-%d')}"
    else:
        text_generation_endpoint = "/generate_weekly_nutrition_overview"
    
    sections = [
        create_text_generation_card(text_generation_endpoint, "Generate Nutrition Overview"),
        create_meals_list(user_id, date) if view_type == "daily" else None,
        create_macro_section(data, view_type),
        create_micro_section(data, view_type),
        create_conditional_section(data, view_type),
        create_metric_overview_section("Hydration", data, water_metrics, view_type=view_type)
    ]
    sections = [section for section in sections if section is not None]
    
    return fh.Div(
        fh.Div(
            *sections,
            cls="w-full space-y-12"
        ),
        cls="w-full"
    )


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


def create_form_section(title, inputs, cls="mb-6"):
    """Helper function to create a form section with a title and inputs"""
    return fh.Section(
        fh.H4(title, cls="font-medium mb-4 text-base-content"),
        fh.Div(
            *inputs,
            cls="grid grid-cols-2 gap-4"
        ),
        cls=cls
    )

def create_meal_breakdown(nutrition_info, meal_time: str, date: str | None = None):
    save_meal_endpoint = f"/save_meal/{date}" if date is not None else "/save_meal"
    return fh.Card(
        fh.Div(
            fh.H4("Ingredients", cls="font-medium mb-2 text-base-content"),
            fh.P(
                nutrition_info.ingredients,
                cls="mb-6 text-base-content"
            ),
            fh.Form(
                hx_post=save_meal_endpoint,
                hx_target="#save-result",
                cls="space-y-6"
            )(
                fh.Input(
                    type="hidden",
                    name="title",
                    value=nutrition_info.title
                ),
                fh.Input(
                    type="hidden",
                    name="ingredients",
                    value=nutrition_info.ingredients
                ),
                fh.Input(
                    type="hidden",
                    name="meal_time",
                    value=meal_time
                ),
                create_nutrition_card(nutrition_info),

                fh.Button(
                    "Save Meal",
                    type="submit",
                    cls="btn btn-neutral w-full"
                ),
                fh.Div(id="save-result", cls="mt-4")
            ),
            cls="p-6"
        ),
        cls="bg-base-200 outline outline-1 outline-base-content rounded-lg shadow-none mt-4 w-full"
    )


def create_nutrition_card(nutrition_info: MealBreakdown | None, card_title: str = "Nutrition Information", title_field: str = "Meal Title"):
    """Create a card containing ingredients text and editable nutrition form"""
    return (
            create_form_section(card_title, [# separate the title from the actual nutriotioanl form so it can be used for multiple purposes
                    create_text_form_input(title_field, "title", nutrition_info.title if nutrition_info else None, input_type="text"),
                    create_text_form_input("Calories (kcal)", "calories", nutrition_info.calories if nutrition_info else None),
                    create_text_form_input("Protein (g)", "protein", nutrition_info.macronutrients.protein if nutrition_info else None),
                    create_text_form_input("Carbohydrates (g)", "carbohydrates", nutrition_info.macronutrients.carbohydrates.total if nutrition_info else None),
                    create_text_form_input("Fat (g)", "fat", nutrition_info.macronutrients.fat.total if nutrition_info else None),
                    create_text_form_input("Fiber (g)", "fiber", nutrition_info.macronutrients.carbohydrates.fiber if nutrition_info else None),
                    create_text_form_input("Vitamin A (IU)", "vitamin_a", nutrition_info.micronutrients.vitamin_a if nutrition_info else None),
                    create_text_form_input("Vitamin C (mg)", "vitamin_c", nutrition_info.micronutrients.vitamin_c if nutrition_info else None),
                    create_text_form_input("Vitamin D (IU)", "vitamin_d", nutrition_info.micronutrients.vitamin_d if nutrition_info else None),
                    create_text_form_input("Calcium (mg)", "calcium", nutrition_info.micronutrients.calcium if nutrition_info else None),
                    create_text_form_input("Iron (mg)", "iron", nutrition_info.micronutrients.iron if nutrition_info else None),
                    create_text_form_input("Potassium (mg)", "potassium", nutrition_info.micronutrients.potassium if nutrition_info else None),
                    create_text_form_input("Sodium (mg)", "sodium", nutrition_info.micronutrients.sodium if nutrition_info else None),
                    create_text_form_input("Creatine (g)", "creatine", nutrition_info.conditional_nutrients.creatine if nutrition_info else None),
                ]
            )
    ) #TODO: make this more dynamic

def supplement_modal(date: datetime.date):
    log_supplement_endpoint = f"/log_supplement_consumption/{date.strftime('%Y-%m-%d')}"
    """Create the supplement tracking modal"""
    return fh.Div(
        fh.Dialog(
            fh.Div(
                # Close button
                fh.Button(
                    "×",
                    cls="absolute right-6 top-6 text-2xl font-light text-base-content hover:text-base-content focus:outline-none focus:ring-0 border-none outline-none z-20",
                    onclick="closeSupplementModal()",
                    style="outline: none; box-shadow: none;"
                ),
                # Initial selection view
                fh.Div(
                    fh.H3("Supplementation", cls="text-xl text-center mb-8 text-base-content mt-4"),
                    fh.Div(
                        # Log existing supplement option
                        fh.Button(
                            "Log existing supplement",
                            cls="btn btn-neutral w-full justify-center text-lg font-light rounded-xl mb-4 outline outline-1 outline-primary-content h-auto py-4",
                            onclick="""
                                document.getElementById('supplement-options').classList.add('hidden');
                                document.getElementById('log-supplement-form').classList.remove('hidden');
                                document.getElementById('supplement-back-button').classList.remove('hidden');
                            """
                        ),
                        # Add new supplement option
                        fh.Button(
                            "Log new supplement",
                            cls="btn btn-neutral w-full justify-center text-lg font-light rounded-xl mb-4 outline outline-1 outline-primary-content h-auto py-4",
                            onclick="""
                                document.getElementById('supplement-options').classList.add('hidden');
                                document.getElementById('supplement-form').classList.remove('hidden');
                                document.getElementById('add-supplement-back-button').classList.remove('hidden');
                            """
                        ),
                        cls="flex flex-col space-y-4 w-full mx-auto"
                    ),
                    id="supplement-options",
                    cls="p-12 px-12"
                ),
                # Form for logging existing supplement
                fh.Div(
                    fh.Button(
                        "←",
                        cls="absolute left-6 top-6 text-2xl font-light text-base-content hover:text-base-content focus:outline-none focus:ring-0 border-none outline-none hidden z-20",
                        onclick="""
                            document.getElementById('supplement-options').classList.remove('hidden');
                            document.getElementById('log-supplement-form').classList.add('hidden');
                            this.classList.add('hidden');
                        """,
                        style="outline: none; box-shadow: none;",
                        id="supplement-back-button"
                    ),
                    fh.H3("Log Supplement", cls="text-xl font-bold text-center mb-8 text-base-content mt-8"),
                    fh.Form(
                        hx_post=log_supplement_endpoint,
                        hx_target="#log-supplement-result",
                        cls="w-[90%] mx-auto space-y-6"
                    )(
                        fh.Div(
                            fh.Label("Select Supplement", cls="label text-base-content"),
                            fh.Select(
                                name="supplement_name",
                                cls="select select-bordered w-full bg-base-200 text-base-content",
                                hx_get="/get_supplements",
                                hx_trigger="load",
                                hx_target="#supplement-select",
                            ),
                            id="supplement-select",
                            cls="form-control"
                        ),
                        fh.Div(
                            fh.Label("Time Consumed", cls="label text-base-content"),
                            fh.Input(
                                type="time",
                                name="time_consumed",
                                value=datetime.now().strftime("%H:%M"),
                                required=True,
                                cls="input input-bordered w-full bg-base-200 text-base-content"
                            ),
                            cls="form-control"
                        ),
                        fh.Div(
                            fh.Label("Servings", cls="label text-base-content"),
                            fh.Input(
                                type="number",
                                name="servings",
                                value="1",
                                step="0.5",
                                min="0",
                                required=True,
                                cls="input input-bordered w-full bg-base-200 text-base-content"
                            ),
                            cls="form-control"
                        ),
                        fh.Button(
                            "Log Supplement",
                            type="submit",
                            cls="btn btn-primary w-full mt-6"
                        ),
                        fh.Div(id="log-supplement-result", cls="mt-4")
                    ),
                    id="log-supplement-form",
                    cls="hidden"
                ),
                # Form for adding new supplement
                fh.Div(
                    fh.Div(
                        fh.Button(
                            "←",
                            cls="text-xl font-light text-base-content hover:text-base-content focus:outline-none focus:ring-0 border-none outline-none",
                            onclick="""
                                document.getElementById('supplement-options').classList.remove('hidden');
                                document.getElementById('supplement-form').classList.add('hidden');
                                this.classList.add('hidden');
                            """,
                            style="outline: none; box-shadow: none;",
                            id="add-supplement-back-button"
                        ),
                        fh.H3("Add New Supplement", cls="text-xl font-bold text-base-content"),
                        fh.Button(
                            "×",
                            cls="text-xl font-light text-base-content hover:text-base-content focus:outline-none focus:ring-0 border-none outline-none",
                            onclick="closeSupplementModal()",
                            style="outline: none; box-shadow: none;"
                        ),
                        cls="flex justify-between items-center px-6 py-4 border-b border-base-content bg-base-200 sticky top-0"
                    ),
                    fh.Div(
                        fh.Form(
                            hx_post="/save_supplement",
                            hx_target="#save-supplement-result",
                            cls="w-[90%] mx-auto"
                        )(
                            fh.Div(
                                fh.Label("Time Taken", cls="label text-base-content"),
                                fh.Input(
                                    type="time",
                                    name="time_consumed",
                                    value=datetime.now().strftime("%H:%M"),
                                    required=True,
                                    cls="input input-bordered w-full bg-base-200 text-base-content"
                                ),
                                cls="form-control mb-4"
                            ),
                            create_nutrition_card(None, title_field="Supplement Name", card_title="Supplement Information"),
                            fh.Button(
                                "Save Supplement",
                                type="submit",
                                cls="btn btn-primary w-full mt-6"
                            ),
                        ),
                        cls="p-6 overflow-y-auto max-h-[70vh]"  # Added overflow and max height
                    ),
                    id="supplement-form",
                    cls="hidden"
                ),
                fh.Div(id="save-supplement-result", cls="mt-4"),
                cls="bg-base-200 rounded-lg relative w-full max-w-lg"  # Reverted to max-w-lg
            ),
            id="supplement-modal",
            cls="modal",
            data_theme="forest"
        ),
        fh.Script("""
            function openSupplementModal() {
                document.getElementById('supplement-modal').showModal();
                document.getElementById('supplement-options').classList.remove('hidden');
                document.getElementById('supplement-form').classList.add('hidden');
                document.getElementById('log-supplement-form').classList.add('hidden');
                document.getElementById('supplement-back-button').classList.add('hidden');
                document.getElementById('add-supplement-back-button').classList.add('hidden');
            }
            
            function closeSupplementModal() {
                document.getElementById('supplement-modal').close();
            }
        """)
    )

def create_meals_list(user_id, date: datetime.date):
    """Create an expandable list of meals for the given date"""
    meals = database_service.get_daily_meals(date, user_id)
    
    if not meals:
        content = fh.P("No meals logged for this day", cls="text-base-content text-center")
    else:
        content = fh.Div(
            *[
                fh.Div(
                    fh.Div(
                        fh.Div(
                            fh.P(meal["meal"].title, cls="text-lg font-bold text-base-content"),
                            fh.Div(
                                fh.Button(
                                    "🗑",  
                                    cls="btn btn-ghost btn-sm px-1 hover:bg-base-300 text-error",
                                    hx_post=f"/delete_meal/{meal['rowid']}",
                                    hx_target="closest div.meal-card",
                                    hx_swap="outerHTML"
                                ),
                                cls="flex items-center gap-1"
                            ),
                            cls="flex justify-between items-center"
                        ),
                        fh.P(
                            f"Time: {meal['meal_time'].strftime('%I:%M %p')}",
                            cls="text-sm text-base-content opacity-80"
                        ),
                        cls="mb-2"
                    ),
                    fh.Div(
                        fh.P(f"Calories: {meal['meal'].calories:.0f} kcal", cls="text-base-content"),
                        fh.P(f"Protein: {meal['meal'].macronutrients.protein:.1f}g", cls="text-base-content"),
                        fh.P(f"Carbs: {meal['meal'].macronutrients.carbohydrates.total:.1f}g", cls="text-base-content"),
                        fh.P(f"Fat: {meal['meal'].macronutrients.fat.total:.1f}g", cls="text-base-content"),
                        cls="grid grid-cols-2 gap-2 mt-2 text-sm"
                    ),
                    cls="p-4 bg-base-300 rounded-lg mb-4 last:mb-0 meal-card"
                )
                for meal in meals
            ],
            cls="mt-4 space-y-2"
        )
    
    return fh.Div(
        fh.Details(
            fh.Summary(
                fh.H3("Meals Logged", cls="text-xl text-base-content inline-block"),
                cls="cursor-pointer hover:opacity-80"
            ),
            content,
            cls="p-6"
        ),
        cls="bg-base-200 outline outline-2 outline-base-content rounded-xl mt-8"
    )

def feedback_form(meal_description: str, meal_time, nutrition_info: MealBreakdown, date: str | None = None):
    """Create a consistent feedback form layout used by both analyze and regenerate functions"""
    return fh.Div(
        fh.Div(
            create_text_input_form(is_feedback=True, original_description=meal_description, original_breakdown=nutrition_info),
            create_meal_breakdown(nutrition_info, meal_time=meal_time, date=date),
            cls="space-y-4 w-[90%] mx-auto"
        ),
        id="text-input" if meal_description != "" else "image-input"  # Use image-input ID if description is empty (image case)
    )

def overview_text(analysis: NutritionFeedback):
    return fh.Card(
        fh.Div(
            fh.P("Summary", cls="text-base-content mb-1 font-bold"),
            fh.P(analysis.summary, cls="text-base-content mb-1"),
            fh.P("Macronutrients", cls="text-base-content mb-1 font-bold"),
            fh.P(analysis.macronutrients, cls="text-base-content mb-1"),
            fh.P("Micronutrients", cls="text-base-content mb-1 font-bold"),
            fh.P(analysis.micronutrients, cls="text-base-content mb-1"),
            fh.P("Suggestions", cls="text-base-content mb-1 font-bold"),
            fh.P(analysis.suggestions, cls="text-base-content mb-1"),
            cls="p-4 space-y-2 mt-2"
        ),
        cls="bg-base-200 outline outline-1 outline-base-content rounded-lg mt-8"
    )
