import json
from datetime import datetime

import fasthtml.common as fh

from fit.nutrition.data import Goals
from fit.nutrition.targets import calculate_all_targets
from fit.web.common import (DB, active_tracker,
                            nutrition_logger, page_outline)
from fit.web.databases import get_daily_cumulative_nutrition, insert_meal


def create_plot(title: str, y_axis_title: str, consumed: float, goal: float, burned: float = None):
    """Create a plot with the provided data"""
    data = []
    
    # Add consumed bar
    data.append({
        "type": "bar",
        "x": ["Today"],
        "y": [consumed],
        "name": "Consumed",
        "marker": {"color": "rgb(59, 130, 246)"}  # Blue
    })
    
    # Add goal bar
    data.append({
        "type": "bar",
        "x": ["Today"],
        "y": [goal],
        "name": "Consumption Goal",
        "marker": {"color": "rgb(147, 197, 253)"}  # Light blue
    })
    
    # Add burned bar for calories
    if burned is not None:
        data.append({
            "type": "bar",
            "x": ["Today"],
            "y": [burned],
            "name": "Burned",
            "marker": {"color": "rgb(239, 68, 68)"}  # Red
        })
    
    plot_data = json.dumps(data)
    plot_layout = create_plot_layout(title, y_axis_title)
    
    return plot_data, plot_layout

def create_plot_layout(title: str, y_axis_title: str):
    """Create the layout configuration for a plot"""
    return json.dumps({
        "title": title,
        "showlegend": True,
        "legend": {"orientation": "h", "y": -0.2},
        "height": 300,
        "margin": {"t": 50, "b": 100},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": "rgb(55, 65, 81)"},
        "yaxis": {"title": y_axis_title},
        "barmode": "group"
    })

def metric_card(title: str, y_axis_title: str, plot_id: str, consumed: float, goal: float, burned: float = None):
    """Create a card containing a metric plot"""
    plot_data, plot_layout = create_plot(title, y_axis_title, consumed, goal, burned)
    
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
            cls="p-4"
        ),
        cls="bg-white shadow-lg rounded-lg h-full"
    )

def create_text_input_form():
    """Create the text input form for meal description"""
    return fh.Card(
        fh.Header(fh.H3("Describe Your Meal", cls="text-xl font-bold mb-4")),
        fh.Form(
            hx_post="/analyze_text",
            hx_target="#text-result",
            cls="space-y-4"
        )(
            fh.Div(
                fh.Label("Meal Description", cls="label"),
                fh.Textarea(
                    name="meal_description",
                    placeholder="Example: I had a grilled chicken sandwich with lettuce, tomato and mayo",
                    rows=3,
                    cls="textarea textarea-bordered w-full"
                ),
                cls="form-control"
            ),
            fh.Button(
                "Analyze Description",
                type="submit",
                cls="btn btn-primary w-full"
            ),
            fh.Div(id="text-result", cls="mt-4")
        )
    )

def create_image_upload_form():
    """Create the image upload form"""
    return fh.Card(
        fh.Header(fh.H3("Upload Food Image", cls="text-xl font-bold mb-4")),
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
                cls="btn btn-primary w-full"
            ),
            fh.Div(id="image-result", cls="mt-4")
        )
    )

def create_modal_content():
    """Create the content for the food tracking modal"""
    return fh.Div(
        # Close button
        fh.Button(
            "×",
            cls="absolute right-4 top-4 text-3xl font-light hover:text-gray-800 z-10",
            onclick="closeModal()"
        ),
        # Scrollable content
        fh.Div(
            create_text_input_form(),
            create_image_upload_form(),
            cls="space-y-6 overflow-y-auto max-h-[80vh] p-6"
        ),
        cls="bg-white rounded-lg shadow-xl relative w-full max-w-lg"
    )

def food_tracking_modal():
    """Create the food tracking modal"""
    return fh.Div(
        # Modal backdrop
        fh.Div(
            cls="fixed inset-0 bg-black bg-opacity-50 transition-opacity hidden",
            id="modal-backdrop",
            onclick="closeModal()"
        ),
        # Modal content
        fh.Div(
            create_modal_content(),
            cls="fixed inset-0 flex items-center justify-center p-4 hidden",
            id="food-modal"
        ),
        # Modal JavaScript
        fh.Script("""
            function openFoodModal() {
                document.getElementById('food-modal').classList.remove('hidden');
                document.getElementById('modal-backdrop').classList.remove('hidden');
                document.body.style.overflow = 'hidden';
            }
            
            function closeModal() {
                document.getElementById('food-modal').classList.add('hidden');
                document.getElementById('modal-backdrop').classList.add('hidden');
                document.body.style.overflow = 'auto';
            }
        """)
    )

def create_fab_menu():
    """Create the floating action button menu"""
    return fh.Div(
        # Sub-buttons (initially hidden)
        fh.Div(
            # Food Entry Button
            fh.Div(
                fh.Span("Food", cls="text-slate-700 text-sm font-medium"),
                fh.Button(
                    fh.Span("🍽️", cls="text-lg"),
                    cls="btn btn-primary btn-circle shadow-lg ml-3",
                    onclick="openFoodModal()"
                ),
                cls="flex items-center justify-end mb-2 opacity-0 transition-all duration-200 translate-y-[30px]",
                id="food-button"
            ),
            # Water Entry Button
            fh.Div(
                fh.Span("Water", cls="text-slate-700 text-sm font-medium"),
                fh.Button(
                    fh.Span("💧", cls="text-lg"),
                    cls="btn btn-primary btn-circle shadow-lg ml-3"
                ),
                cls="flex items-center justify-end mb-2 opacity-0 transition-all duration-200 translate-y-[30px]",
                id="water-button"
            ),
            cls="absolute bottom-16 right-0 transition-all duration-200"
        ),
        # Main FAB
        fh.Button(
            fh.Span("+", cls="text-2xl transition-transform duration-200"),
            cls="btn btn-primary btn-circle shadow-lg",
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

def create_metrics_grid(data):
    """Create the grid of metric cards"""
    return fh.Div(
        fh.Div(
            # Row 1
            fh.Div(
                metric_card(
                    "Calories", "Calories", "calories-plot",
                    data["calories"]["consumed"],
                    data["calories"]["goal"],
                    data["calories"]["burned"]
                ),
                metric_card(
                    "Protein", "Protein (g)", "protein-plot",
                    data["protein"]["consumed"],
                    data["protein"]["goal"]
                ),
                cls="grid grid-cols-2 gap-6 mb-6"
            ),
            # Row 2
            fh.Div(
                metric_card(
                    "Carbohydrate", "Carbs (g)", "carbs-plot",
                    data["carbs"]["consumed"],
                    data["carbs"]["goal"]
                ),
                metric_card(
                    "Fat", "Fat (g)", "fat-plot",
                    data["fat"]["consumed"],
                    data["fat"]["goal"]
                ),
                cls="grid grid-cols-2 gap-6 mb-6"
            ),
            # Row 3 (centered water card)
            fh.Div(
                fh.Div(
                    metric_card(
                        "Water", "Water (oz)", "water-plot",
                        data["water"]["consumed"],
                        data["water"]["goal"]
                    ),
                    cls="w-1/2"
                ),
                cls="flex justify-center"
            ),
            cls="w-full"
        ),
        cls="w-full"
    )

def get():
    """Return the nutritional overview page content"""
    # Example data - replace with actual data from your database
    
    calories_burned = active_tracker.get_daily_calories_burned(datetime.today())
    goals = calculate_all_targets(calories_burned, Goals.MAINTAIN) # goal hardcoded for now

    macros = get_daily_cumulative_nutrition(DB, datetime.date(datetime.today()))
    
    data = {
        "calories": {"consumed": 1800, "goal": goals["calories"], "burned": calories_burned},
        "protein": {"consumed": 80, "goal": goals["protein"]},
        "carbs": {"consumed": 200, "goal": goals["carbs"]},
        "fat": {"consumed": 60, "goal": goals["fat"]},
        "water": {"consumed": 40, "goal": 64}  # in oz
    }

    
    print(macros)

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

def NutritionCard(nutrition_info):
    """Helper function to create a consistent nutrition display card"""
    macros = [
        ("Calories", f"{nutrition_info.calories} kcal"),
        ("Protein", f"{nutrition_info.protein}g"),
        ("Carbs", f"{nutrition_info.carbs}g"),
        ("Fat", f"{nutrition_info.fat}g"),
        ("Fiber", f"{nutrition_info.fiber}g"),
    ]
    
    vitamins = [
        ("Vitamin A", f"{nutrition_info.vitamin_a} IU"),
        ("Vitamin C", f"{nutrition_info.vitamin_c} mg"),
        ("Vitamin D", f"{nutrition_info.vitamin_d} IU"),
    ]
    
    minerals = [
        ("Calcium", f"{nutrition_info.calcium} mg"),
        ("Iron", f"{nutrition_info.iron} mg"),
        ("Potassium", f"{nutrition_info.potassium} mg"),
        ("Sodium", f"{nutrition_info.sodium} mg"),
    ]
    
    return fh.Card(
        fh.Header(
            fh.H3(nutrition_info.summary, cls="text-lg font-semibold text-center mb-4")
        ),
        create_nutrition_section("Macronutrients", macros),
        create_nutrition_section("Vitamins", vitamins),
        create_nutrition_section("Minerals", minerals, cls=""),
        cls="bg-white shadow-lg rounded-lg p-6"
    )


async def analyze_image(food_image: fh.UploadFile):
    """Handle image upload and analysis"""
    nutrition_info = nutrition_logger.image_macros(food_image)
    
    insert_meal(DB, "Image Upload", nutrition_info)
    
    return NutritionCard(nutrition_info)


async def analyze_text(meal_description: str):
    """Handle meal description analysis"""
    nutrition_info = nutrition_logger.natural_language_macros(meal_description)
    
    insert_meal(DB, meal_description, nutrition_info)

    return NutritionCard(nutrition_info)


