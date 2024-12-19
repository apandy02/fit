from datetime import datetime

import fasthtml.common as fh

from fit.nutrition.data import Goals, MealBreakdown
from fit.nutrition.targets import calculate_macro_targets
from fit.web.common import (DB, active_tracker, nutrition_logger, nutritionist,
                            page_outline, micronutrient_goals, Markdown)
from fit.web.databases import (get_daily_cumulative_nutrition, get_daily_meals,
                               insert_meal)
from fit.web.food_plots import create_plot


def metric_card(title: str, y_axis_title: str, plot_id: str, consumed: float, goal: float, burned: float = None, show_analysis: bool = True):
    """Create a card containing a metric plot"""
    plot_data, plot_layout = create_plot(title, y_axis_title, consumed, goal, burned)
    
    analysis_text = None
    if show_analysis:
        macro_name = title.lower()
        if macro_name == "carbohydrates":
            macro_name = "carbohydrate"
        analysis_text = nutritionist.macro_analysis(macro_name, consumed, goal)
    
    return fh.Card(
        fh.Div(
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
            fh.P(analysis_text, cls="text-sm text-slate-300 mt-4") if analysis_text else None,
            cls="p-4"
        ),
        cls="bg-slate-800 rounded-lg h-full text-slate-200"
    )

def create_text_input_form():
    """Create the text input form for meal description"""
    return fh.Card(
        fh.Div(
            fh.Header(
                fh.H3("Describe Your Meal", cls="text-xl font-bold text-slate-200"),
                cls="mb-6"
            ),
            fh.Form(
                hx_post="/analyze_text",
                hx_target="#text-result",
                cls="space-y-4"
            )(
                fh.Div(
                    fh.Label("Meal Description", cls="label text-slate-200"),
                    fh.Textarea(
                        name="meal_description",
                        placeholder="Example: I had a grilled chicken sandwich with lettuce, tomato and mayo",
                        rows=3,
                        cls="textarea textarea-bordered w-full bg-slate-700 text-slate-200 placeholder-slate-400"
                    ),
                    cls="form-control"
                ),
                fh.Button(
                    "Analyze Description",
                    type="submit",
                    cls="btn bg-primary"
                ),
                fh.Div(id="text-result", cls="mt-4")
            ),
            cls="p-6"
        ),
        cls="bg-base-100 shadow-lg rounded-lg"
    )

def create_image_upload_form():
    """Create the image upload form"""
    return fh.Card(
        fh.Div(
            fh.Header(
                fh.H3("Upload Food Image", cls="text-xl font-bold text-slate-200"),
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
        cls="bg-base-100 shadow-lg rounded-lg"
    )

def create_modal_content():
    """Create the content for the food tracking modal"""
    return fh.Div(
        # Close button
        fh.Button(
            "×",
            cls="absolute right-4 top-4 text-xl font-light text-blue-400 hover:text-blue-300 focus:outline-none focus:ring-0 focus:ring-offset-0 border-none outline-none z-10",
            onclick="closeModal()",
            style="outline: none; box-shadow: none;"
        ),
        # Back button (shown only when a form is visible)
        fh.Button(
            "←",
            cls="absolute left-4 top-4 text-xl font-light text-blue-400 hover:text-blue-300 focus:outline-none focus:ring-0 focus:ring-offset-0 border-none outline-none hidden z-10",
            onclick="showInputSelection()",
            style="outline: none; box-shadow: none;",
            id="back-button"
        ),
        # Initial selection view
        fh.Div(
            fh.Div(
                fh.H3("How would you like to log your meal?", cls="text-xl font-bold text-center mb-8 text-slate-200"),
                fh.Div(
                    # Image upload option
                    fh.Button(
                        fh.Div(
                            fh.Img(
                                src="/static/images/camera.png",
                                cls="h-12 w-auto object-contain mb-3"
                            ),
                            fh.P("Upload an image", cls="text-slate-200 mb-2"),
                            cls="flex flex-col items-center justify-center h-full"
                        ),
                        cls="p-6 bg-slate-800 rounded-lg hover:bg-slate-700 transition-colors w-full focus:outline-none mb-4 h-32",
                        onclick="showInputForm('image')"
                    ),
                    # Text description option
                    fh.Button(
                        fh.P("Describe it", cls="text-slate-200 text-lg"),
                        cls="p-6 bg-slate-800 rounded-lg hover:bg-slate-700 transition-colors w-full flex items-center justify-center focus:outline-none h-32",
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
            cls="space-y-6 overflow-y-auto max-h-[80vh]"
        ),
        cls="bg-base-100 rounded-lg relative w-full max-w-lg"
    )

def food_tracking_modal():
    """Create the food tracking modal"""
    return fh.Div(
        fh.Div(
            cls="fixed inset-0 bg-slate-800 bg-opacity-20 transition-opacity hidden",
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
                fh.Span(name, cls="text-slate-300 text-sm font-medium"),
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
        fh.H2("Nutritional Overview", cls="text-3xl font-bold text-center mb-6"),
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

def create_metric_overview_section(title, metrics_data, metrics_config):
    """Create a metrics overview section with configurable metrics"""
    metric_rows = [metrics_config[i:i+2] for i in range(0, len(metrics_config), 2)]
    
    return fh.Section(
        fh.H3(f"{title} Overview", cls="text-2xl font-bold text-center mb-8 text-slate-200"),
        fh.Div(
            *[fh.Div(
                *[metric_card(
                    metric["name"],
                    f"{metric['name']} ({metric['unit']})" if metric["unit"] else metric["name"],
                    metric["plot_id"],
                    metrics_data[metric["column_name"]]["consumed"],
                    metrics_data[metric["column_name"]]["goal"],
                    metrics_data[metric["column_name"]].get("burned")
                ) for metric in row],
                cls="grid grid-cols-2 gap-6 mb-6"
            ) for row in metric_rows],
            cls="w-full"
        ),
        cls="w-full"
    )

def create_macro_section(data):
    """Create the macronutrient metrics section"""
    macro_metrics = [
        {"name": "Calories", "column_name": "calories", "unit": "", "plot_id": "calories-plot"},
        {"name": "Protein", "column_name": "protein", "unit": "g", "plot_id": "protein-plot"},
        {"name": "Carbohydrates", "column_name": "carbs", "unit": "g", "plot_id": "carbs-plot"},
        {"name": "Fat", "column_name": "fat", "unit": "g", "plot_id": "fat-plot"}
    ]
    return create_metric_overview_section("Macronutrient", data, macro_metrics)

def create_micro_section(data):
    """Create the micronutrient metrics section"""
    micro_metrics = [
        {"name": "Vitamin A", "column_name": "vitamin_a", "unit": "IU", "plot_id": "vitamin-a-plot"},
        {"name": "Vitamin C", "column_name": "vitamin_c", "unit": "mg", "plot_id": "vitamin-c-plot"},
        {"name": "Iron", "column_name": "iron", "unit": "mg", "plot_id": "iron-plot"},
        {"name": "Calcium", "column_name": "calcium", "unit": "mg", "plot_id": "calcium-plot"}
    ]
    return create_metric_overview_section("Micronutrient", data, micro_metrics)

def create_water_section(data):
    """Create the water metrics section"""
    return fh.Section(
        fh.H3("Hydration Overview", cls="text-2xl font-bold text-center mb-6 text-slate-200"),
        fh.Div(
            fh.Div(
                metric_card(
                    "Water", "Water (oz)", "water-plot",
                    data["water"]["consumed"],
                    data["water"]["goal"],
                    show_analysis=False
                ),
                cls="w-1/2 mx-auto"  # Centered with max width of 50%
            ),
            cls="w-full"
        ),
        cls="w-full"
    )

def create_metrics_grid(data):
    """Create the grid of metric cards"""
    return fh.Div(
        fh.Div(
            create_overview_card(),
            create_macro_section(data),
            create_micro_section(data),
            create_water_section(data),
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
                    cls="btn btn-primary",
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
        cls="bg-slate-800 rounded-lg mb-8 text-slate-200"
    )

async def generate_overview():
    """Generate the daily overview analysis"""
    today = datetime.date(datetime.today())
    meals = get_daily_meals(DB, today)

    calories_burned = active_tracker.get_daily_calories_burned(datetime.today())
    targets = calculate_macro_targets(calories_burned, Goals.MAINTAIN)
    targets.update(micronutrient_goals)
    analysis = nutritionist.daily_io_analysis(meals, targets)
    print(analysis)
            
    return fh.Card(
        fh.Div(
            *[
                fh.Div(
                    fh.P(Markdown(line.strip()), cls="mb-1 text-slate-300"),
                    cls="mb-2"
                )
                for line in analysis.split('\n')
                if line.strip() 
            ],
            cls="p-4 space-y-2"
        ),
        cls="bg-slate-800 rounded-lg mt-4"
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
        "water": {"consumed": 40, "goal": 64}
    }

    content = fh.Article(
        fh.Div(
            create_page_header(),
            create_metrics_grid(data),
            food_tracking_modal(),
            create_fab_menu(),
            cls="max-w-6xl mx-auto p-6"
        )
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
        fh.Label(label_text, cls="label text-slate-200"),
        fh.Input(
            type=input_type,
            name=input_name,
            value=formatted_value,
            step=step if input_type == "number" else None,
            cls="input input-bordered w-full bg-slate-700 text-slate-200"
        ),
        cls="form-control"
    )

def create_form_section(title, inputs, cls="mb-6"):
    """Helper function to create a form section with a title and inputs"""
    return fh.Section(
        fh.H4(title, cls="font-medium mb-4 text-slate-200"),
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
            fh.H4("Ingredients", cls="font-medium mb-2 text-slate-200"),
            fh.P(
                nutrition_info.ingredients,
                cls="mb-6 text-slate-200"
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
        cls="bg-slate-800 rounded-lg p-6"
    )

async def analyze_text(meal_description: str):
    """Handle meal description analysis"""
    nutrition_info = nutrition_logger.natural_language_macros(meal_description)
    return create_nutrition_card(nutrition_info)

async def analyze_image(food_image: fh.UploadFile):
    """Handle image upload and analysis"""
    nutrition_info = nutrition_logger.image_macros(food_image)
    return create_nutrition_card(nutrition_info)

async def save_meal(request: fh.Request):
    """Save the meal with user-adjusted nutrition values"""
    try:
        form = await request.form()
        print(form)
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
