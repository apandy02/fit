import fasthtml.common as fh
from fit.nutrition.assistants import NutritionTracker
from datetime import datetime

app, rt = fh.fast_app()
DB_PATH = "data/nutrition.db"

def init_db():
    """
    Initialize the database and create tables if they don't exist.
    """
    db = fh.database(DB_PATH)

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

                fiber=float,
                vitamin_a=float,
                vitamin_c=float,
                vitamin_d=float,
                calcium=float,
                iron=float,
                potassium=float,
                sodium=float,
                
            ),
            pk='datetime_entered' # TODO: change to a more suitable primary key
        )

    measurements_table = db.t.measurements  
    if measurements_table not in db.t:
        measurements_table.create(
            dict(
                datetime=str,
                height=float,
                weight=float,
            ),
            pk='datetime' # TODO: change to a more suitable primary key
        )

    return meals_table, measurements_table


MEALS_TABLE, MEASUREMENTS_TABLE = init_db()

nutrition_tracker = NutritionTracker()

@rt("/")
def get():
    return fh.Titled("AI Fitness Tracker",
        fh.Article(
            fh.Form(hx_post="/analyze_image", hx_target="#image-result")(
                fh.H2("Upload Food Image"),
                fh.Input(type="file", name="food_image", accept="image/*"),
                fh.Button("Analyze Image", type="submit", cls='primary'),
                fh.Div(id="image-result")
            ),
            fh.Form(hx_post="/analyze_text", hx_target="#text-result")(
                fh.H2("Describe Your Meal"),
                fh.Textarea(
                    name="meal_description",
                    placeholder="Example: I had a grilled chicken sandwich with lettuce, tomato and mayo",
                    rows=3
                ),
                fh.Button("Analyze Description", type="submit", cls='primary'),
                fh.Div(id="text-result")
            )
        )
    )

def NutritionCard(nutrition_info):
    """Helper function to create a consistent nutrition display card"""
    return fh.Card(
        fh.Header(fh.H3(nutrition_info.summary)),
        fh.Section(
            fh.H4("Macronutrients"),
            fh.Ul(
                fh.Li(f"Calories: {nutrition_info.calories} kcal"),
                fh.Li(f"Protein: {nutrition_info.protein}g"),
                fh.Li(f"Carbs: {nutrition_info.carbs}g"),
                fh.Li(f"Fat: {nutrition_info.fat}g"),
                fh.Li(f"Fiber: {nutrition_info.fiber}g"),
            )
        ),
        fh.Section(
            fh.H4("Micronutrients"),
            fh.Ul(
                fh.Li(f"Vitamin A: {nutrition_info.vitamin_a} mg"),
                fh.Li(f"Vitamin C: {nutrition_info.vitamin_c} mg"),
                fh.Li(f"Vitamin D: {nutrition_info.vitamin_d} mg"),
                fh.Li(f"Calcium: {nutrition_info.calcium} mg"),
                fh.Li(f"Iron: {nutrition_info.iron} mg"),
                fh.Li(f"Potassium: {nutrition_info.potassium} mg"),
                fh.Li(f"Sodium: {nutrition_info.sodium} mg"),
            )
        )
    )

@rt
async def analyze_image(food_image: fh.UploadFile):
    """Handle image upload and analysis"""
    nutrition_info = nutrition_tracker.image_macros(food_image)
    
    MEALS_TABLE.insert(
        datetime_entered=datetime.now().isoformat(),
        meal_time=datetime.now().isoformat(),  # change to user specified later 
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
    
    MEALS_TABLE.insert(
        datetime_entered=datetime.now().isoformat(),
        meal_time=datetime.now().isoformat(), # change to user specified later 
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

fh.serve() 