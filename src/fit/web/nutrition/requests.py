import io
from datetime import datetime

import fasthtml.common as fh
from PIL import Image

import fit.nutrition.assistants as assistants
import fit.web.common as common
import fit.web.nutrition.ui as ui
from fit.nutrition.data_models import (Carbohydrates, ConditionalNutrients,
                                       Fats, Macronutrients, MealBreakdown,
                                       Micronutrients, NutritionalInformation,
                                       WeightGoal)
from fit.nutrition.targets import (calculate_macro_targets,
                                   estimate_daily_water_intake)
from fit.trackers.base import FitnessTracker
from fit.trackers.manager import tracker_factory
from fit.utils.calendar import get_current_week_dates
from fit.web.common import database_service, micronutrient_goals


def get_daily_overview(session, date: str = None):
    """Return the nutritional overview page content"""
    tracker = tracker_factory(session["tracker"], session["access_token"])
    if not date:
        date = datetime.today().date()
    else:
        try:
            date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            date = datetime.today().date()
    
    data = get_daily_nutrition_data(date, tracker, session["user_id"])
    return overview_page_content(session, data, "daily", date)

def get_weekly_overview(session):
    """Return the weekly nutritional overview page content"""
    tracker = tracker_factory(session["tracker"], session["access_token"])
    week = get_current_week_dates()
    data = get_weekly_nutrition_data(week, tracker, session["user_id"])
    date = datetime.today().date()
    return overview_page_content(session, data, "weekly", date)

def overview_page_content(session, data: list[dict], current_view: str, date: datetime.date = None):
    menu_items = [
        ("Food", "🍽️", "openFoodModal()"),
        ("Water", "💧", "openWaterModal()"), 
        ("Supplement", "💊", "openSupplementModal()")
    ]

    water_metrics = [
        {"name": "Water", "column_name": "water", "unit": "ml", "plot_id": "water-plot"}
    ]

    content = fh.Article(
        fh.Div(
            ui.create_page_header(current_view, date),
            ui.create_metrics_grid(session["user_id"], data, water_metrics, current_view, date),
            ui.food_tracking_modal(date),
            common.create_fab_menu(menu_items),
            cls="max-w-6xl mx-auto p-6"
        ),
        cls="bg-base-100",
    )
    return common.page_outline(1, "Nutritional Overview", True, True, content)

def get_weekly_nutrition_data(week: list[datetime], tracker: FitnessTracker, user_id: int):
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
            daily_data = get_daily_nutrition_data(date, tracker, user_id)
            for metric, values in daily_data.items():
                for key, value in values.items():
                    data[metric][key].extend(value)
    
    return data

def get_daily_nutrition_data(date: datetime, tracker: FitnessTracker, user_id: int):
    """Get the current nutrition data for display"""
    calories_burned = tracker.get_daily_calories_burned(date)
    goals = calculate_macro_targets(calories_burned, WeightGoal.MAINTAIN)
    daily_consumption = database_service.get_daily_cumulative_nutrition(date, user_id)
    water_consumed = database_service.get_daily_water_consumption(date, user_id)
    user_info = database_service.get_profile_data(user_id)
    measurements = database_service.get_latest_user_measurements(user_id)
    water_goal = estimate_daily_water_intake(measurements, user_info, calories_burned)
    
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

async def analyze_text(request: fh.Request, date: str | None = None):
    """Handle meal description analysis"""
    form = await request.form()
    meal_description = form["meal_description"]
    meal_time = form["meal_time"]
    nutrition_info = assistants.natural_language_nutritional_breakdown(meal_description).content[0].parsed
    meal_time_obj = datetime.strptime(meal_time, "%H:%M").time()
    return ui.feedback_form(meal_description, meal_time_obj, nutrition_info, date)

async def analyze_image(food_image: fh.UploadFile, additional_context: str, meal_time: str, date: str | None = None):
    """Handle image upload and analysis"""
    
    contents = await food_image.read()
    image = Image.open(io.BytesIO(contents))
    nutrition_info = assistants.vision_nutritional_breakdown(image, additional_context).content[0].parsed
    meal_time_obj = datetime.strptime(meal_time, "%H:%M").time()

    return ui.feedback_form(additional_context, meal_time_obj, nutrition_info, date)

async def save_meal(session, request: fh.Request, date: str | None = None):
    """Save the meal with user-adjusted nutrition values"""
    user_id = session["user_id"]
    try:
        form = await request.form()
        if date is not None:
            date = datetime.today().date()

        meal_time = form["meal_time"]

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
        database_service.insert_meal(form["title"], nutrition_info, date, meal_time, user_id)
        return fh.Response(headers={"HX-Redirect": "/nutrition"}, status_code=200)
    
    except Exception as e:
        return fh.P(
            f"Error saving meal: {str(e)}",
            cls="text-red-500 font-semibold text-center"
        )

async def delete_meal(meal_id: int):
    """Delete a meal from the database and return updated meals list"""
    try:
        success = database_service.delete_meal(meal_id)
    except Exception as e:
        print(f"Error deleting meal: {e}")
        return fh.P(
            f"Error deleting meal: {str(e)}",
            cls="text-red-500 font-semibold text-center"
        )
    if success:
        return None  

    else:
        return fh.P(
            "Error deleting meal",
            cls="text-red-500 font-semibold text-center"
        )

async def save_supplement(session, request: fh.Request):
    """Save the supplement with user-adjusted nutrition values"""
    user_id = session["user_id"]
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
        database_service.insert_supplement(
            name=form["summary"], consumption_time=form["time_consumed"], nutritional_info=nutrition_info, user_id=user_id
        )
        
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

async def get_supplements(session):
    """Get all supplements for the dropdown"""
    supplements = database_service.get_supplement_names(session["user_id"])
    return fh.Select(
        *[
            fh.Option(
                name,
                value=name,
            ) for name in supplements
        ],
        name="supplement_name",
        cls="select select-bordered w-full bg-base-200 text-base-content",
        required=True
    )

async def log_supplement_consumption(session, request: fh.Request, date: str | None = None):
    """Log a supplement consumption entry"""
    user_id = session["user_id"]
    try:
        form = await request.form()
        supplement_name = form["supplement_name"]
        time_consumed = form["time_consumed"]
        
        supplement_info = database_service.get_supplement(supplement_name)
        database_service.insert_supplement(
            name=supplement_name,
            consumption_time=time_consumed,
            nutritional_info=supplement_info,
            user_id=user_id
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

async def regenerate_analysis(request: fh.Request, feedback: str, original_description: str, original_breakdown: str):
    """Regenerate analysis based on feedback"""
    form = await request.form()
    feedback = form["feedback"]
    original_description = form["original_description"]
    original_breakdown = form["original_breakdown"]

    improved_info = assistants.improve_breakdown(original_breakdown, feedback).content[0].parsed
    meal_time_obj = datetime.now().time()
    meal_datetime = datetime.combine(datetime.today().date(), meal_time_obj).isoformat()
    date = datetime.today().date()
    
    return ui.feedback_form(original_description, meal_datetime, improved_info, date)

async def generate_weekly_overview(session):
    """
    Generate the weekly overview analysis by getting the user's meals for the week,
    their dietary restrictions, their calories burned for the week, and calculating their targets for the week.
    Then, passing these to the weekly_io_analysis LMP.
    """
    analysis = generate_overview(session, None, weekly=True)

    if isinstance(analysis, str):
        return fh.P(analysis, cls="text-base-content mt-2")
    
    return ui.overview_text(analysis)

async def generate_daily_overview(session, date: str | None = None):
    """
    Generate the daily overview analysis by getting the user's meals for the day,
    their dietary restrictions, their calories burned for the day, and calculating their targets for the day.
    Then, passing these to the daily_io_analysis LMP.
    """
    try:
        analysis = generate_overview(session, date, weekly=False)
    except assistants.NoMealsLoggedError as e:
        return fh.P(str(e), cls="text-base-content mt-2")
        
    return ui.overview_text(analysis)

def generate_overview(session, date: str | None = None, weekly: bool = False):
    """Get the overview data for the given date or week"""
    if weekly:
        days = get_current_week_dates()
        meals = get_weekly_meals(days, session["user_id"])
    else:
        if date is None:
            days = [datetime.today().date()]
        else:
            try:
                days = [datetime.strptime(date, "%Y-%m-%d").date()]
            except ValueError:
                days = [datetime.today().date()]
        meals = database_service.get_daily_meals(days[0], session["user_id"])
    
    nutritional_data = get_user_nutritional_data_for_dates(session, days)
    if weekly:
        return assistants.weekly_io_analysis(meals, nutritional_data["targets"], nutritional_data["restrictions"]).content[0].parsed
    else:
        return assistants.daily_io_analysis(meals, nutritional_data["targets"][0], nutritional_data["restrictions"]).content[0].parsed

async def nutrition_redirect(request: fh.Request):
    """Redirect to the nutrition page"""
    form = await request.form()
    current_view = form["time_filter"]
    if current_view == "daily":
        return fh.Response(headers={"HX-Redirect": "/nutrition"}, status_code=200)
    elif current_view == "weekly":
        return fh.Response(headers={"HX-Redirect": "/nutrition/weekly"}, status_code=200)

async def get_nutrient_suggestions(session, nutrient: str):
    """Generate meal suggestions based on a specific nutrient"""
    daily_nutrition = database_service.get_daily_cumulative_nutrition(datetime.today().date(), session["user_id"])
    nutritional_data = get_user_nutritional_data_for_dates(session, [datetime.today().date()])
    user_preferences = assistants.summarize_user_preferences(database_service.get_all_meal_summaries(session["user_id"])) # TODO: cache the output of this so that we aren't calling it every time
    kitchen_inventory = database_service.get_inventory(session["user_id"])
    recommendations = assistants.make_recommendations(
        consumption=daily_nutrition,
        targets=nutritional_data["targets"][0],
        target_nutrient=nutrient,
        restrictions=nutritional_data["restrictions"],
        user_preferences=user_preferences,
        kitchen_inventory=kitchen_inventory
    ).content[0].parsed

    return ui.create_meal_suggestions(recommendations)
def get_user_nutritional_data_for_dates(session, dates: list[datetime.date]):
    """
    Get the user's nutritional data for the given dates.
    Args:
        session: the user's session
        dates: a list of the dates to get the nutritional data for
    Returns:
        - dict:
            - targets: a list of the user's targets for the given dates
            - daily_nutrition: a list of the user's daily nutrition for the given dates
            - weight_goal: the user's weight goal
            - restrictions: the user's dietary restrictions
            - calories_burned: the user's calories burned for the given dates
    """
    tracker = tracker_factory(session["tracker"], session["access_token"])
    weight_goal = WeightGoal(database_service.get_weight_goal(session["user_id"]))
    calories_burned = [tracker.get_daily_calories_burned(day) for day in dates]
    targets = [calculate_macro_targets(calories_burned, weight_goal) for calories_burned in calories_burned]
    [target.update(micronutrient_goals) for target in targets]
    
    return {
        "targets": targets,
        "daily_nutrition": [database_service.get_daily_cumulative_nutrition(day, session["user_id"]) for day in dates],
        "weight_goal": weight_goal, 
        "restrictions": database_service.get_dietary_restrictions(session["user_id"]),
        "calories_burned": calories_burned
    }

async def log_water(session, request: fh.Request, date: str | None = None):
    """Save water consumption entry"""
    try:
        form = await request.form()
        time_consumed = form["time_consumed"]
        
        if date is None:
            date = datetime.today().date()
        time_obj = datetime.strptime(time_consumed, "%H:%M").time()
        database_service.insert_water_consumption(
            water_consumed_ml=form["amount"], date_consumed=date, time_consumed=time_obj, user_id=session["user_id"]
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
    
def get_weekly_meals(week: list[datetime], user_id: int):
    """
    Get the meals for a given week.
    Returns a dict mapping "date_str" -> [list of meals].
    """
    return {
        str(day): database_service.get_daily_meals(day, user_id) for day in week
    }
