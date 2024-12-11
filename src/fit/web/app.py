from fasthtml.common import *
from fit.nutrition.data import NutritionalInfo
from fit.nutrition.assistants import NutritionTracker
from datetime import datetime

app, rt = fast_app()
DB_PATH = "data/nutrition.db"

def init_db():
    """
    Initialize the database and create tables if they don't exist.
    """
    db = database(DB_PATH)

    meals_table = db.t.meals
    if meals_table not in db.t:
        meals_table.create(
            dict(
                datetime_entered=str,
                meal_time=str,
                user_description=str,
                llm_summary=str,
                calories=float,
                protein=float,
                carbs=float,
                fat=float,
                vitamin_a=float,
                vitamin_c=float,
                vitamin_d=float,
                calcium=float,
                iron=float,
                potassium=float,
                sodium=float,
                fiber=float
            )
        )

    measurements_table = db.t.measurements  
    if measurements_table not in db.t:
        measurements_table.create(
            dict(
                datetime=str,
                height=float,
                weight=float,
            )
        )

    return meals_table, measurements_table


MEALS_TABLE, MEASUREMENTS_TABLE = init_db()

nutrition_tracker = NutritionTracker()

@rt("/")
def get():
    return Titled("AI Fitness Tracker",
        Article(
            # Image upload form
            Form(hx_post="/analyze_image", hx_target="#image-result")(
                H2("Upload Food Image"),
                Input(type="file", name="food_image", accept="image/*"),
                Button("Analyze Image", type="submit", cls='primary'),
                Div(id="image-result")
            ),
            
            # Natural language form
            Form(hx_post="/analyze_text", hx_target="#text-result")(
                H2("Describe Your Meal"),
                Textarea(
                    name="meal_description",
                    placeholder="Example: I had a grilled chicken sandwich with lettuce, tomato and mayo",
                    rows=3
                ),
                Button("Analyze Description", type="submit", cls='primary'),
                Div(id="text-result")
            )
        )
    )

def NutritionCard(nutrition_info):
    """Helper function to create a consistent nutrition display card"""
    return Card(
        Header(H3(nutrition_info.summary)),
        # Macros section
        Section(
            H4("Macronutrients"),
            Ul(
                Li(f"Calories: {nutrition_info.calories} kcal"),
                Li(f"Protein: {nutrition_info.protein}g"),
                Li(f"Carbs: {nutrition_info.carbs}g"),
                Li(f"Fat: {nutrition_info.fat}g"),
                Li(f"Fiber: {nutrition_info.fiber}g"),
            )
        ),
        # Vitamins section
        Section(
            H4("Vitamins"),
            Ul(
                Li(f"Vitamin A: {nutrition_info.vitamin_a} IU"),
                Li(f"Vitamin C: {nutrition_info.vitamin_c} mg"),
                Li(f"Vitamin D: {nutrition_info.vitamin_d} IU"),
            )
        ),
        # Minerals section
        Section(
            H4("Minerals"),
            Ul(
                Li(f"Calcium: {nutrition_info.calcium} mg"),
                Li(f"Iron: {nutrition_info.iron} mg"),
                Li(f"Potassium: {nutrition_info.potassium} mg"),
                Li(f"Sodium: {nutrition_info.sodium} mg"),
            )
        )
    )

@rt
async def analyze_image(food_image: UploadFile):
    """Handle image upload and analysis"""
    nutrition_info = nutrition_tracker.image_macros(food_image)
    
    # Store in database
    MEALS_TABLE.insert(
        datetime_entered=datetime.now().isoformat(),
        meal_time=datetime.now().isoformat(),  # User could specify meal time in future
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

@rt
async def analyze_text(meal_description: str):
    """Handle meal description analysis"""
    nutrition_info = nutrition_tracker.natural_language_macros(meal_description)
    print(nutrition_info)
    
    # Store in database
    MEALS_TABLE.insert(
        datetime_entered=datetime.now().isoformat(),
        meal_time=datetime.now().isoformat(),  # User could specify meal time in future
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

serve() 