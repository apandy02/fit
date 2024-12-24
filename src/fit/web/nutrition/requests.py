from datetime import datetime

import fasthtml.common as fh

import fit.web.common as common
import fit.web.databases as databases
import fit.web.nutrition.ui as ui
from fit.nutrition.data import Goals, MealBreakdown
from fit.nutrition.targets import calculate_macro_targets
from fit.utils.calendar import get_current_week_dates
from fit.web.common import (DB, active_tracker, micronutrient_goals,
                            nutrition_logger, nutritionist)


def get_daily_overview():
    """Return the nutritional overview page content"""
    date = datetime.today().date()
    data = get_daily_nutrition_data(date)
    return overview_page_content(data, "daily")

    

def get_weekly_overview():
    """Return the weekly nutritional overview page content"""
    week = get_current_week_dates()
    data = get_weekly_nutrition_data(week)
    return overview_page_content(data, "weekly")


def overview_page_content(data: list[dict], current_view: str):
    menu_items = [
        ("Food", "🍽️", "openFoodModal()"),
        ("Water", "💧", None)  # No handler yet
    ]

    visible_metrics = databases.get_visible_metrics(DB, "default") # TODO: get user_id from session, hardcoded for now
    water_metrics = [
        {"name": "Water", "column_name": "water", "unit": "oz", "plot_id": "water-plot"}
    ]

    content = fh.Article(
        fh.Div(
            ui.create_page_header(current_view),
            ui.create_metrics_grid(data, visible_metrics, water_metrics, current_view),
            ui.food_tracking_modal(),
            common.create_fab_menu(menu_items),
            cls="max-w-6xl mx-auto p-6"
        ),
        cls="bg-base-100",
    )
    return common.page_outline(1, "Nutritional Overview", content)

def get_weekly_nutrition_data(date: datetime):
    """Get the current nutrition data for display"""
    week = get_current_week_dates()
    data = {
        "calories": {"consumed": [], "goal": [], "burned": []},
        "protein": {"consumed": [], "goal": []},
        "carbs": {"consumed": [], "goal": []}, 
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
    return {
        "calories": {"consumed": [daily_consumption.calories], "goal": [goals["calories"]], "burned": [calories_burned]},
        "protein": {"consumed": [daily_consumption.protein], "goal": [goals["protein"]]},
        "carbs": {"consumed": [daily_consumption.carbs], "goal": [goals["carbs"]]},
        "fat": {"consumed": [daily_consumption.fat], "goal": [goals["fat"]]},
        "vitamin_a": {"consumed": [daily_consumption.vitamin_a], "goal": [micronutrient_goals["vitamin_a"]]},
        "vitamin_c": {"consumed": [daily_consumption.vitamin_c], "goal": [micronutrient_goals["vitamin_c"]]},
        "iron": {"consumed": [daily_consumption.iron], "goal": [micronutrient_goals["iron"]]},
        "calcium": {"consumed": [daily_consumption.calcium], "goal": [micronutrient_goals["calcium"]]},
        "water": {"consumed": [40], "goal": [64]},
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

async def analyze_text(meal_description: str, meal_time: str):
    """Handle meal description analysis"""
    nutrition_info = nutrition_logger.natural_language_macros(meal_description)
    today = datetime.today().date()
    meal_time_obj = datetime.strptime(meal_time, "%H:%M").time()
    meal_datetime = datetime.combine(today, meal_time_obj).isoformat()
    
    return fh.Card(
        fh.Div(
            fh.Div(
                ui.create_text_input_form(is_feedback=True, original_description=meal_description)
            ),
            fh.Div(
                ui.create_nutrition_card(nutrition_info, meal_time=meal_datetime),
                id="nutrition-card"
            ),
            cls="p-6"
        ),
        cls="bg-base-200 rounded-lg",
        id="text-input"  # Important: keep the same ID for proper replacement
    )

async def analyze_image(food_image: fh.UploadFile, meal_time: str):
    """Handle image upload and analysis"""
    nutrition_info = nutrition_logger.image_macros(food_image)
    # Create ISO format datetime for meal time
    today = datetime.today().date()
    meal_time_obj = datetime.strptime(meal_time, "%H:%M").time()
    meal_datetime = datetime.combine(today, meal_time_obj).isoformat()
    
    return ui.create_nutrition_card(nutrition_info, meal_time=meal_datetime)

async def save_meal(request: fh.Request):
    """Save the meal with user-adjusted nutrition values"""
    try:
        form = await request.form()
        # The meal_time is already in ISO format from the hidden input
        meal_datetime = form["meal_time"]
        
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
        databases.insert_meal(DB, form["summary"], nutrition_info, meal_datetime)
        
        return fh.Div(
            fh.P(
                "Meal saved successfully!",
                cls="text-green-500 font-semibold text-center mb-4"
            ),
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

async def reset_text_form():
    """Reset the text form to its original state"""
    return ui.create_text_input_form(is_feedback=False)

async def regenerate_analysis(feedback: str, original_description: str):
    """Regenerate analysis based on feedback"""
    original_info = nutrition_logger.natural_language_macros(original_description)
    improved_info = nutrition_logger.improve_breakdown(original_info, feedback)
    return fh.Card(
        fh.Div(
            fh.Div(
                ui.create_text_input_form(is_feedback=True)
            ),
            fh.Div(
                ui.create_nutrition_card(improved_info),
                id="nutrition-card"
            ),
            cls="p-6"
        ),
        cls="bg-base-200 rounded-lg",
        id="text-input"  # Important: keep the same ID for proper replacement
    )

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

    analysis = nutritionist.weekly_io_analysis(meals, targets, dietary_restrictions)
    
    return fh.Card(
        fh.Div(
            *[
                fh.Div(
                    fh.P(fh.NotStr(line.strip()), cls="text-primary-content mb-1"),
                    cls="mb-2"
                )
                for line in analysis.split('\n')
                if line.strip() 
            ],
            cls="p-4 space-y-2 mt-2"
        ),
        cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg mt-4"
    )

async def generate_daily_overview():
    """
    Generate the daily overview analysis by getting the user's meals for the day,
    their dietary restrictions, their calories burned for the day, and calculating their targets for the day.
    Then, passing these to the daily_io_analysis LMP.
    """
    today = datetime.date(datetime.today())
    meals = databases.get_daily_meals(DB, today)
    
    dietary_restrictions = databases.get_dietary_restrictions(DB, "default")

    calories_burned = active_tracker.get_daily_calories_burned(datetime.today())
    targets = calculate_macro_targets(calories_burned, Goals.MAINTAIN)
    targets.update(micronutrient_goals)
    analysis = nutritionist.daily_io_analysis(meals, targets, dietary_restrictions)
    
    return fh.Card(
        fh.Div(
            *[
                fh.Div(
                    fh.P(fh.NotStr(line.strip()), cls="text-primary-content mb-1"),
                    cls="mb-2"
                )
                for line in analysis.split('\n')
                if line.strip() 
            ],
            cls="p-4 space-y-2 mt-2"
        ),
        cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg mt-4"
    )

async def nutrition_redirect(request: fh.Request):
    """Redirect to the nutrition page"""
    form = await request.form()
    current_view = form["time_filter"]
    if current_view == "daily":
        return fh.Response(headers={"HX-Redirect": "/nutrition"}, status_code=200)
    elif current_view == "weekly":
        return fh.Response(headers={"HX-Redirect": "/nutrition/weekly"}, status_code=200)