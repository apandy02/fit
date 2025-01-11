import io
from datetime import datetime

import fasthtml.common as fh
from PIL import Image

import fit.nutrition.assistants as assistants
import fit.web.common as common
import fit.web.databases as databases
import fit.web.nutrition.ui as ui
from fit.nutrition.data_models import (Carbohydrates, ConditionalNutrients,
                                       Fats, Goals, Macronutrients,
                                       MealBreakdown, Micronutrients,
                                       NutritionalInformation)
from fit.nutrition.targets import (calculate_macro_targets,
                                   estimate_daily_water_intake)
from fit.utils.calendar import get_current_week_dates
from fit.web.common import DB, active_tracker, micronutrient_goals


def get_daily_overview(date: str = None):
    """Return the nutritional overview page content"""
    if date is None:
        date = datetime.today().date()
    else:
        try:
            date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            # If invalid date format, default to today
            date = datetime.today().date()
    
    data = get_daily_nutrition_data(date)
    return overview_page_content(data, "daily", date)

    

def get_weekly_overview():
    """Return the weekly nutritional overview page content"""
    week = get_current_week_dates()
    data = get_weekly_nutrition_data(week)
    return overview_page_content(data, "weekly")


def overview_page_content(data: list[dict], current_view: str, date: datetime.date = None):
    menu_items = [
        ("Food", "🍽️", "openFoodModal()"),
        ("Water", "💧", "openWaterModal()"),  # Updated to use water modal
        ("Supplement", "💊", "openSupplementModal()")
    ]

    visible_metrics = databases.get_visible_metrics(DB, "default") # TODO: get user_id from session, hardcoded for now
    water_metrics = [
        {"name": "Water", "column_name": "water", "unit": "ml", "plot_id": "water-plot"}
    ]

    content = fh.Article(
        fh.Div(
            ui.create_page_header(current_view, date),
            ui.create_metrics_grid(data, visible_metrics, water_metrics, current_view, date),
            common.create_overview_card(current_view, date),
            ui.food_tracking_modal(),
            common.create_fab_menu(menu_items),
            cls="max-w-6xl mx-auto p-6"
        ),
        cls="bg-base-100",
    )
    return common.page_outline(1, "Nutritional Overview", content)

def get_weekly_nutrition_data(week: list[datetime]):
    """Get the current nutrition data for display"""
    data = {
        "calories": {"consumed": [], "goal": [], "burned": []},
        "protein": {"consumed": [], "goal": []},
        "carbohydrates": {"consumed": [], "goal": []}, 
        "fat": {"consumed": [], "goal": []},
        "vitamin_a": {"consumed": [], "goal": []},
        "vitamin_c": {"consumed": [], "goal": []},
        "iron": {"consumed": [], "goal": []},
        "calcium": {"consumed": [], "goal": []},
        "water": {"consumed": [], "goal": []},
        "creatine": {"consumed": [], "goal": []}
    }
    
    today = datetime.today().date()
    for date in week:
        if date > today:
            # For future dates, extend with 0s
            for metric in data:
                for key in data[metric]:
                    data[metric][key].extend([0])
        else:
            daily_data = get_daily_nutrition_data(date)
            for metric, values in daily_data.items():
                for key, value in values.items():
                    data[metric][key].extend(value)
    
    return data

def get_daily_nutrition_data(date: datetime):
    """Get the current nutrition data for display"""
    calories_burned = active_tracker.get_daily_calories_burned(date)
    goals = calculate_macro_targets(calories_burned, Goals.MAINTAIN)
    daily_consumption = databases.get_daily_cumulative_nutrition(DB, date)
    water_consumed = databases.get_daily_water_consumption(DB, date)
    user_info = databases.get_user_data(DB)
    measurements = databases.get_latest_user_measurements(DB)
    water_goal = estimate_daily_water_intake(measurements["weight"], user_info["gender"], calories_burned)
    
    return {
        "calories": {"consumed": [daily_consumption.calories], "goal": [goals["calories"]], "burned": [calories_burned]},
        "protein": {"consumed": [daily_consumption.macronutrients.protein], "goal": [goals["protein"]]},
        "carbohydrates": {"consumed": [daily_consumption.macronutrients.carbohydrates.total], "goal": [goals["carbohydrates"]]},
        "fat": {"consumed": [daily_consumption.macronutrients.fat.total], "goal": [goals["fat"]]},
        "vitamin_a": {"consumed": [daily_consumption.micronutrients.vitamin_a], "goal": [micronutrient_goals["vitamin_a"]]},
        "vitamin_c": {"consumed": [daily_consumption.micronutrients.vitamin_c], "goal": [micronutrient_goals["vitamin_c"]]},
        "iron": {"consumed": [daily_consumption.micronutrients.iron], "goal": [micronutrient_goals["iron"]]},
        "calcium": {"consumed": [daily_consumption.micronutrients.calcium], "goal": [micronutrient_goals["calcium"]]},
        "water": {"consumed": [water_consumed], "goal": [water_goal]},
        "creatine": {"consumed": [2.0], "goal": [5.0]}
    }

async def toggle_dropdown(dropdown_id: str):
    """Toggle the visibility of a dropdown"""
    visible = databases.get_visible_metrics(DB, "default")
    if "macro" in dropdown_id:
        all_metrics = ["Calories", "Protein", "Carbohydrates", "Fat"]
    elif "micro" in dropdown_id:
        all_metrics = ["Vitamin A", "Vitamin C", "Iron", "Calcium"]
    elif "conditional" in dropdown_id:
        all_metrics = ["Creatine"]

    metric_column_names = [metric.lower().replace(" ", "_") for metric in all_metrics]
    hidden = [metric for metric in metric_column_names if metric not in visible]

    # Return the dropdown with its content
    return fh.Div(
        *[
            fh.A(
                metric["name"],
                cls="block w-full text-left px-4 py-2 text-sm text-primary-content hover:bg-base-200 outline  cursor-pointer",
                onclick=f"""
                    fetch('/show_metric/{metric}', {{method: 'POST'}})
                        .then(response => response.text())
                        .then(html => {{
                            document.getElementById('metrics-container').outerHTML = html;
                            document.getElementById('{dropdown_id}').classList.add('hidden');
                        }});
                    return false;
                """,
                href="#"
            )
            for metric in hidden
        ],
        cls="absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-base-200 outline  ring-1 ring-black ring-opacity-5 z-10 block",  # Removed hidden class
        id=dropdown_id
    )

def feedback_form(meal_description: str, meal_datetime: datetime, nutrition_info: MealBreakdown):
    """Create a consistent feedback form layout used by both analyze and regenerate functions"""
    return fh.Div(
        fh.Div(
            ui.create_text_input_form(is_feedback=True, original_description=meal_description),
            ui.create_meal_breakdown(nutrition_info, meal_time=meal_datetime),
            cls="space-y-4 w-[90%] mx-auto"
        ),
        id="text-input"
    )

async def analyze_text(meal_description: str, meal_time: str):
    """Handle meal description analysis"""
    nutrition_info = assistants.natural_language_macros(meal_description).content[0].parsed
    today = datetime.today().date()
    meal_time_obj = datetime.strptime(meal_time, "%H:%M").time()
    meal_datetime = datetime.combine(today, meal_time_obj).isoformat()
    
    return feedback_form(meal_description, meal_datetime, nutrition_info)

async def analyze_image(food_image: fh.UploadFile, additional_context: str, meal_time: str):
    """Handle image upload and analysis"""
    
    contents = await food_image.read()
    image = Image.open(io.BytesIO(contents))
    nutrition_info = assistants.image_macros(image, additional_context).content[0].parsed
    today = datetime.today().date()
    meal_time_obj = datetime.strptime(meal_time, "%H:%M").time()
    meal_datetime = datetime.combine(today, meal_time_obj).isoformat()
    
    return feedback_form(additional_context, meal_datetime, nutrition_info)

async def save_meal(request: fh.Request):
    """Save the meal with user-adjusted nutrition values"""
    try:
        form = await request.form()
        meal_datetime = form["meal_time"]
        macronutrients = Macronutrients(
            protein=form["protein"],
            carbohydrates=Carbohydrates(
                total=form["carbohydrates"], 
                fiber=form["fiber"], 
                total_sugar=0, # TODO: incorporate submacros
                added_sugar=0
            ),
            fat=Fats(
                total=form["fat"],
                saturated=0, # TODO: incorporate submacros
                trans=0 # TODO: incorporate submacros
            )
        )
        conditional_nutrients = ConditionalNutrients(
            creatine=form["creatine"]
        )
        micronutrients = Micronutrients(
            vitamin_a=form["vitamin_a"],
            vitamin_c=form["vitamin_c"],
            vitamin_d=form["vitamin_d"],
            calcium=form["calcium"],
            iron=form["iron"],
            potassium=form["potassium"],
            sodium=form["sodium"]
        )
        nutrition_info = MealBreakdown(
            title=form["title"],
            ingredients=form["ingredients"],
            calories=form["calories"],
            macronutrients=macronutrients,
            micronutrients=micronutrients,
            conditional_nutrients=conditional_nutrients
        )    
        databases.insert_meal(DB, form["title"], nutrition_info, meal_datetime)
        
        return fh.Response(headers={"HX-Redirect": "/nutrition"}, status_code=200)
    except Exception as e:
        return fh.P(
            f"Error saving meal: {str(e)}",
            cls="text-red-500 font-semibold text-center"
        )
    

async def save_supplement(request: fh.Request):
    """Save the supplement with user-adjusted nutrition values"""
    try:
        form = await request.form()

        nutrition_info = NutritionalInformation(
            calories=form["calories"],
            protein=form["protein"],
            carbohydrates=form["carbohydrates"],
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
        databases.insert_supplement(DB, name=form["summary"], consumption_time=form["time_consumed"], nutritional_info=nutrition_info)
        
        return fh.Div(
            fh.P(
                "Supplement saved successfully!",
                cls="text-green-500 font-semibold text-center mb-4"
            ),
            fh.Script("""
                // Show success message briefly
                setTimeout(() => {
                    // Close the modal
                    closeSupplementModal();
                    
                    // Force a new GET request to the current page
                    window.location.href = window.location.pathname;
                }, 1000);
            """)
        )
    except Exception as e:
        return fh.P(
            f"Error saving supplement: {str(e)}",
            cls="text-red-500 font-semibold text-center"
        )

async def get_supplements():
    """Get all supplements for the dropdown"""
    supplements = databases.get_supplement_names(DB)
    return fh.Select(
        *[
            fh.Option(
                name,
                value=name,
            ) for name in supplements
        ],
        name="supplement_name",
        cls="select select-bordered w-full bg-base-200 text-primary-content",
        required=True
    )

async def log_supplement_consumption(request: fh.Request):
    """Log a supplement consumption entry"""
    try:
        form = await request.form()
        supplement_name = form["supplement_name"]
        time_consumed = form["time_consumed"]
        
        supplement_info = databases.get_supplement(DB, supplement_name)
        databases.insert_supplement(
            DB, 
            name=supplement_name,
            consumption_time=time_consumed,
            nutritional_info=supplement_info
        )
        
        return fh.Div(
            fh.P(
                "Supplement logged successfully!",
                cls="text-green-500 font-semibold text-center mb-4"
            ),
            fh.Script("""
                // Show success message briefly
                setTimeout(() => {
                    // Close the modal
                    closeSupplementModal();
                    
                    // Force a new GET request to the current page
                    window.location.href = window.location.pathname;
                }, 1000);
            """)
        )
    except Exception as e:
        return fh.P(
            f"Error logging supplement: {str(e)}",
            cls="text-red-500 font-semibold text-center"
        )

async def reset_text_form():
    """Reset the text form to its original state"""
    return ui.create_text_input_form(is_feedback=False)

async def regenerate_analysis(feedback: str, original_description: str):
    """Regenerate analysis based on feedback"""
    original_info = assistants.natural_language_macros(original_description).content[0].parsed #TODO: why are we re-running this?
    improved_info = assistants.improve_breakdown(original_info, feedback).content[0].parsed # todo: maybe the parsing should be done in the assistant
    
    # Create ISO format datetime for meal time
    today = datetime.today().date()
    meal_time_obj = datetime.now().time()
    meal_datetime = datetime.combine(today, meal_time_obj).isoformat()
    
    return feedback_form(original_description, meal_datetime, improved_info)

async def hide_metric(plot_id: str):
    """Hide a metric by removing it from visible_metrics"""
    visible_metrics = databases.get_visible_metrics(DB, "default")

    if plot_id in visible_metrics:
        visible_metrics.remove(plot_id)
        databases.set_visible_metrics(DB, visible_metrics, "default")
    return ""  # Return empty string to remove the card

async def show_metric(plot_id: str, view_type: str):
    """Show a previously hidden metric"""
    visible_metrics = databases.get_visible_metrics(DB, "default")
    column_name = plot_id.replace("-plot", "").replace("_", "")
    if column_name not in visible_metrics:
        visible_metrics.append(column_name)
        databases.set_visible_metrics(DB, visible_metrics, "default")
    
    date = datetime.today().date()
    return ui.create_metrics_grid(get_daily_nutrition_data(date), visible_metrics, view_type)


# TODO: the next two functions are doing a lot of the same work, find a way to refactor
async def generate_weekly_overview():
    """
    Generate the weekly overview analysis by getting the user's meals for the week,
    their dietary restrictions, their calories burned for the week, and calculating their targets for the week.
    Then, passing these to the weekly_io_analysis LMP.
    """
    week = get_current_week_dates()
    meals = databases.get_weekly_meals(DB, week)
    
    dietary_restrictions = databases.get_dietary_restrictions(DB, "default")
    calories_burned = [active_tracker.get_daily_calories_burned(day) for day in week]
    targets = [calculate_macro_targets(calories_burned, Goals.MAINTAIN) for calories_burned in calories_burned]
    [target.update(micronutrient_goals) for target in targets]
 
    analysis = assistants.weekly_io_analysis(meals, targets, dietary_restrictions).content[0].parsed

    if isinstance(analysis, str):
        return fh.P(analysis, cls="text-primary-content mt-2")
    
    return fh.Card(
        fh.Div(
            fh.P("Summary", cls="text-primary-content mb-1 font-bold"),
            fh.P(analysis.summary, cls="text-primary-content mb-1"),
            fh.P("Macronutrients", cls="text-primary-content mb-1 font-bold"),
            fh.P(analysis.macronutrients, cls="text-primary-content mb-1"),
            fh.P("Micronutrients", cls="text-primary-content mb-1 font-bold"),
            fh.P(analysis.micronutrients, cls="text-primary-content mb-1"),
            fh.P("Suggestions", cls="text-primary-content mb-1 font-bold"),
            fh.P(analysis.suggestions, cls="text-primary-content mb-1"),
            cls="p-4 space-y-2 mt-2"
        ),
        cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg mt-8"
    )

async def generate_daily_overview(date: str | None = None):
    """
    Generate the daily overview analysis by getting the user's meals for the day,
    their dietary restrictions, their calories burned for the day, and calculating their targets for the day.
    Then, passing these to the daily_io_analysis LMP.
    """
    if date is None:
        date_obj = datetime.today().date()
    else:
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            date_obj = datetime.today().date()
            
    meals = databases.get_daily_meals(DB, date_obj)
    
    dietary_restrictions = databases.get_dietary_restrictions(DB, "default")

    calories_burned = active_tracker.get_daily_calories_burned(date_obj)
    targets = calculate_macro_targets(calories_burned, Goals.MAINTAIN)
    targets.update(micronutrient_goals)
    analysis = assistants.daily_io_analysis(meals, targets, dietary_restrictions).content[0].parsed

    if isinstance(analysis, str):
        return fh.P(analysis, cls="text-primary-content mt-2")
        
    return fh.Card(
        fh.Div(
            fh.P("Summary", cls="text-primary-content mb-1 font-bold"),
            fh.P(analysis.summary, cls="text-primary-content mb-1"),
            fh.P("Macronutrients", cls="text-primary-content mb-1 font-bold"),
            fh.P(analysis.macronutrients, cls="text-primary-content mb-1"),
            fh.P("Micronutrients", cls="text-primary-content mb-1 font-bold"),
            fh.P(analysis.micronutrients, cls="text-primary-content mb-1"),
            fh.P("Suggestions", cls="text-primary-content mb-1 font-bold"),
            fh.P(analysis.suggestions, cls="text-primary-content mb-1"),
            cls="p-4 space-y-2 mt-2"
        ),
        cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg mt-8"
    )

async def nutrition_redirect(request: fh.Request):
    """Redirect to the nutrition page"""
    form = await request.form()
    current_view = form["time_filter"]
    if current_view == "daily":
        return fh.Response(headers={"HX-Redirect": "/nutrition"}, status_code=200)
    elif current_view == "weekly":
        return fh.Response(headers={"HX-Redirect": "/nutrition/weekly"}, status_code=200)

async def get_nutrient_suggestions(nutrient: str):
    """Generate meal suggestions based on a specific nutrient"""
    today = datetime.today().date()
    daily_nutrition = databases.get_daily_cumulative_nutrition(DB, today)
    
    calories_burned = active_tracker.get_daily_calories_burned(today)
    targets = calculate_macro_targets(calories_burned, Goals.MAINTAIN)
    targets.update(micronutrient_goals)
    restrictions = databases.get_dietary_restrictions(DB, "default")
    user_preferences = assistants.summarize_user_preferences(databases.get_all_meal_summaries(DB)) # TODO: cache the output of this so that we aren't calling it every time

    recommendations = assistants.make_recommendations(
        consumption=daily_nutrition,
        targets=targets,
        target_nutrient=nutrient,
        restrictions=restrictions,
        user_preferences=user_preferences
    ).content[0].parsed
    return fh.Div(
        fh.H4("Suggestions", cls="text-lg font-bold mb-1 text-primary-content text-center"),
        fh.Div(
            fh.Ul(
                *[
                    fh.Li(
                        fh.Div(
                            fh.P(meal.title, cls="font-medium text-primary-content text-sm text-center font-bold mb-1"),
                            fh.P(meal.ingredients, cls="text-primary-content text-xs text-center"),
                            cls="mb-3"
                        ),
                        cls="list-none"
                    ) for meal in recommendations.meals
                ],
                cls="list-none p-0"
            ),
            cls="outline outline-1 outline-primary-content rounded-lg p-4 max-h-[200px] overflow-y-auto mt-3"
        ),
        cls="bg-base-200 p-4 rounded-lg"
    )

async def log_water(request: fh.Request):
    """Save water consumption entry"""
    try:
        form = await request.form()
        time_consumed = form["time_consumed"]
        
        today = datetime.today().date()
        time_obj = datetime.strptime(time_consumed, "%H:%M").time()
        databases.insert_water_consumption(
            database=DB, water_consumed_ml=form["amount"], date_consumed=today, time_consumed=time_obj
        )
        
        return fh.Div(
            fh.P(
                "Water logged successfully!",
                cls="text-green-500 font-semibold text-center mb-4"
            ),
            fh.Script("""
                // Show success message briefly
                setTimeout(() => {
                    // Close the modal
                    closeWaterModal();
                    
                    // Reload the page to show updated data
                    window.location.reload();
                }, 1000);
            """)
        )
    except Exception as e:
        return fh.P(
            f"Error logging water: {str(e)}",
            cls="text-red-500 font-semibold text-center"
        )