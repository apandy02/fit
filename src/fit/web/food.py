import fasthtml.common as fh
from datetime import datetime
from fit.web.common import MEALS_TABLE, nutrition_tracker, page_outline


def get():
    """Return the food tracking page content"""
    content = fh.Article(
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
            cls="space-y-6 max-w-lg mx-auto p-6"
        )
    )
    return page_outline(1, "Food Tracking", content)


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

