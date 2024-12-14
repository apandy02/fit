import fasthtml.common as fh
import json
from datetime import datetime
from fit.web.common import MEALS_TABLE, nutrition_tracker, page_outline

def create_empty_plot(title: str, y_axis_title: str):
    """Create an empty plot with consistent styling"""
    plot_data = json.dumps([
        {"type": "bar", "x": [], "y": [], "name": f"{y_axis_title} Consumed"},
        {"type": "bar", "x": [], "y": [], "name": f"{y_axis_title} Goal"}
    ])
    
    plot_layout = json.dumps({
        "title": title,
        "showlegend": True,
        "legend": {"orientation": "h", "y": -0.2},
        "height": 300,
        "margin": {"t": 50, "b": 100},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": "rgb(55, 65, 81)"},
        "yaxis": {"title": y_axis_title}
    })
    
    return plot_data, plot_layout

def metric_card(title: str, y_axis_title: str, plot_id: str):
    """Create a card containing a metric plot"""
    plot_data, plot_layout = create_empty_plot(title, y_axis_title)
    
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

def food_tracking_modal():
    """Create the food tracking modal content"""
    return fh.Div(
        # Modal backdrop
        fh.Div(
            cls="fixed inset-0 bg-black bg-opacity-50 transition-opacity hidden",
            id="modal-backdrop",
            onclick="closeModal()"
        ),
        # Modal content
        fh.Div(
            fh.Div(
                # Close button
                fh.Button(
                    "×",
                    cls="absolute right-4 top-4 text-3xl font-light hover:text-gray-800 z-10",
                    onclick="closeModal()"
                ),
                # Scrollable content
                fh.Div(
                    # Text input section
                    fh.Card(
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
                    ),
                    # Image upload section
                    fh.Card(
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
                    ),
                    cls="space-y-6 overflow-y-auto max-h-[80vh] p-6"
                ),
                cls="bg-white rounded-lg shadow-xl relative w-full max-w-lg"
            ),
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

def get():
    """Return the nutritional overview page content"""
    content = fh.Article(
        fh.Div(
            # Title and Time Filter
            fh.Div(
                fh.H2(
                    "Nutritional Overview",
                    cls="text-3xl font-bold text-center mb-6"
                ),
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
            ),
            
            # Metrics Grid
            fh.Div(
                fh.Div(
                    # Row 1
                    fh.Div(
                        # Calories
                        metric_card(
                            "Calories",
                            "Calories",
                            "calories-plot"
                        ),
                        # Protein
                        metric_card(
                            "Protein",
                            "Protein (g)",
                            "protein-plot"
                        ),
                        cls="grid grid-cols-2 gap-6 mb-6"
                    ),
                    # Row 2
                    fh.Div(
                        # Carbs
                        metric_card(
                            "Carbohydrate",
                            "Carbs (g)",
                            "carbs-plot"
                        ),
                        # Fat
                        metric_card(
                            "Fat",
                            "Fat (g)",
                            "fat-plot"
                        ),
                        cls="grid grid-cols-2 gap-6 mb-6"
                    ),
                    # Row 3 (centered water card)
                    fh.Div(
                        fh.Div(
                            # Water
                            metric_card(
                                "Water",
                                "Water (oz)",
                                "water-plot"
                            ),
                            cls="w-1/2"
                        ),
                        cls="flex justify-center"
                    ),
                    cls="w-full"
                ),
                cls="w-full"
            ),
            
            # Food tracking modal
            food_tracking_modal(),
            
            # Floating Action Button Menu
            fh.Div(
                # Sub-buttons (initially hidden)
                fh.Div(
                    # Food Entry Button
                    fh.Div(
                        fh.Span(
                            "Food",
                            cls="text-slate-700 text-sm font-medium"
                        ),
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
                        fh.Span(
                            "Water",
                            cls="text-slate-700 text-sm font-medium"
                        ),
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
                            // Show buttons
                            foodBtn.style.opacity = '1';
                            waterBtn.style.opacity = '1';
                            foodBtn.style.transform = 'translate(0, -30px)';
                            waterBtn.style.transform = 'translate(0, -15px)';
                        } else {
                            // Hide buttons
                            foodBtn.style.opacity = '0';
                            waterBtn.style.opacity = '0';
                            foodBtn.style.transform = 'translate(0, 15px)';
                            waterBtn.style.transform = 'translate(0, 15px)';
                        }
                    """
                ),
                cls="fixed bottom-8 right-8"
            ),
            
            cls="max-w-6xl mx-auto p-6"
        )
    )
    return page_outline(1, "Nutritional Overview", content)


def NutritionCard(nutrition_info):
    """Helper function to create a consistent nutrition display card"""
    return fh.Card(
        fh.Header(
            fh.H3(nutrition_info.summary, cls="text-lg font-semibold text-center mb-4")
        ),
        # Macros section
        fh.Section(
            fh.H4("Macronutrients", cls="font-medium mb-2"),
            fh.Ul(
                fh.Li(
                    fh.Span("Calories: ", cls="font-medium"),
                    f"{nutrition_info.calories} kcal",
                    cls="mb-1"
                ),
                fh.Li(
                    fh.Span("Protein: ", cls="font-medium"),
                    f"{nutrition_info.protein}g",
                    cls="mb-1"
                ),
                fh.Li(
                    fh.Span("Carbs: ", cls="font-medium"),
                    f"{nutrition_info.carbs}g",
                    cls="mb-1"
                ),
                fh.Li(
                    fh.Span("Fat: ", cls="font-medium"),
                    f"{nutrition_info.fat}g",
                    cls="mb-1"
                ),
                fh.Li(
                    fh.Span("Fiber: ", cls="font-medium"),
                    f"{nutrition_info.fiber}g",
                    cls="mb-1"
                ),
                cls="list-none"
            ),
            cls="mb-4"
        ),
        # Vitamins section
        fh.Section(
            fh.H4("Vitamins", cls="font-medium mb-2"),
            fh.Ul(
                fh.Li(
                    fh.Span("Vitamin A: ", cls="font-medium"),
                    f"{nutrition_info.vitamin_a} IU",
                    cls="mb-1"
                ),
                fh.Li(
                    fh.Span("Vitamin C: ", cls="font-medium"),
                    f"{nutrition_info.vitamin_c} mg",
                    cls="mb-1"
                ),
                fh.Li(
                    fh.Span("Vitamin D: ", cls="font-medium"),
                    f"{nutrition_info.vitamin_d} IU",
                    cls="mb-1"
                ),
                cls="list-none"
            ),
            cls="mb-4"
        ),
        # Minerals section
        fh.Section(
            fh.H4("Minerals", cls="font-medium mb-2"),
            fh.Ul(
                fh.Li(
                    fh.Span("Calcium: ", cls="font-medium"),
                    f"{nutrition_info.calcium} mg",
                    cls="mb-1"
                ),
                fh.Li(
                    fh.Span("Iron: ", cls="font-medium"),
                    f"{nutrition_info.iron} mg",
                    cls="mb-1"
                ),
                fh.Li(
                    fh.Span("Potassium: ", cls="font-medium"),
                    f"{nutrition_info.potassium} mg",
                    cls="mb-1"
                ),
                fh.Li(
                    fh.Span("Sodium: ", cls="font-medium"),
                    f"{nutrition_info.sodium} mg",
                    cls="mb-1"
                ),
                cls="list-none"
            )
        ),
        cls="bg-white shadow-lg rounded-lg p-6"
    )


async def analyze_image(food_image: fh.UploadFile):
    """Handle image upload and analysis"""
    nutrition_info = nutrition_tracker.image_macros(food_image)
    
    MEALS_TABLE.insert(
        datetime_entered=datetime.now().isoformat(),
        meal_time=datetime.now().isoformat(),
        user_description="Image Upload",
        llm_summary=nutrition_info.summary,
        calories=nutrition_info.calories,
        protein=nutrition_info.protein,
        carbs=nutrition_info.carbs,
        fat=nutrition_info.fat,
        vitamin_a=nutrition_info.vitamin_a,
        vitamin_c=nutrition_info.vitamin_c,
        vitamin_d=nutrition_info.vitamin_d,
        calcium=nutrition_info.calcium,
        iron=nutrition_info.iron,
        potassium=nutrition_info.potassium,
        sodium=nutrition_info.sodium,
        fiber=nutrition_info.fiber
    )
    
    return NutritionCard(nutrition_info)


async def analyze_text(meal_description: str):
    """Handle meal description analysis"""
    nutrition_info = nutrition_tracker.natural_language_macros(meal_description)
    
    MEALS_TABLE.insert(
        datetime_entered=datetime.now().isoformat(),
        meal_time=datetime.now().isoformat(),
        user_description=meal_description,
        llm_summary=nutrition_info.summary,
        calories=nutrition_info.calories,
        protein=nutrition_info.protein,
        carbs=nutrition_info.carbs,
        fat=nutrition_info.fat,
        vitamin_a=nutrition_info.vitamin_a,
        vitamin_c=nutrition_info.vitamin_c,
        vitamin_d=nutrition_info.vitamin_d,
        calcium=nutrition_info.calcium,
        iron=nutrition_info.iron,
        potassium=nutrition_info.potassium,
        sodium=nutrition_info.sodium,
        fiber=nutrition_info.fiber
    )

    return NutritionCard(nutrition_info)

