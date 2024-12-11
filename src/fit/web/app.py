from fasthtml.common import *

app, rt = fast_app()

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
        Header(H3("Nutritional Information")),
        Ul(
            Li(f"Calories: {nutrition_info.calories}"),
            Li(f"Protein: {nutrition_info.protein}g"),
            Li(f"Carbs: {nutrition_info.carbs}g"),
            Li(f"Fat: {nutrition_info.fat}g")
        )
    )

@rt
async def analyze_image(food_image: UploadFile):
    """Handle image upload and analysis"""
    # Here you would integrate with your image analysis system
    # For now, return a placeholder response
    return NutritionCard(NutritionalInfo(
        calories=500,
        protein=25,
        carbs=45,
        fat=20
    ))

@rt
async def analyze_text(meal_description: str):
    """Handle meal description analysis"""
    # Here you would integrate with your text analysis system
    # For now, return a placeholder response
    return NutritionCard(NutritionalInfo(
        calories=600,
        protein=30,
        carbs=50,
        fat=25
    ))

serve() 