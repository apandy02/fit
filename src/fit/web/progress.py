import json
from datetime import datetime

import fasthtml.common as fh
from fit.nutrition.data import Goals
from fit.web.common import DB, create_fab_menu, create_modal, page_outline


def get():
    """Return the progress tracking page content"""
    measurements = DB.execute("SELECT datetime, weight FROM measurements ORDER BY datetime").fetchall()
    plot_data, plot_layout = create_weight_plot(measurements)

    fab_buttons = [
        ("Weight", "⚖️", "openModal('weight-modal')"),
        ("Height", "📏", "openModal('height-modal')"),
        ("Goal", "🎯", "openModal('goal-modal')")
    ]
    
    content = fh.Article(
        fh.Div(
            fh.Card(
                fh.Header(
                    fh.H3("Your Progress", cls="text-2xl font-bold text-center mb-2 text-primary-content"),
                    fh.P(
                        "Track your weight changes over time",
                        cls="text-slate-400 text-center"
                    ),
                    cls="mb-6 bg-base-200"
                ),
                fh.Div(
                    fh.Div(id="weight-plot", cls="w-full"),
                    fh.Script(
                        f"""
                        Plotly.newPlot(
                            'weight-plot',
                            {plot_data},
                            {plot_layout},
                            {{responsive: true}}
                        );
                        """
                    ),
                    cls="p-4 bg-base-200 rounded-lg shadow-lg"
                ),
                fh.Div(
                    fh.Div(
                        fh.H4("Statistics", cls="text-lg font-semibold mb-4 text-primary-content"),
                        create_stats_grid(measurements),
                    ),
                    cls="mt-8"
                ),
                cls="bg-base-200 shadow-lg rounded-lg p-6"
            ),
            create_fab_menu(fab_buttons),
            create_modal(create_progress_modal_card("Update Weight", create_weight_form, "weight-modal"),),
            create_modal(create_progress_modal_card("Update Height", create_height_form, "height-modal")),
            create_modal(create_progress_modal_card("Change Goal", create_goal_form, "goal-modal")),
            cls="max-w-4xl mx-auto p-6 bg-base-100"
        ),
        cls="bg-base-100"
    )
    return page_outline(2, "Progress Tracking", content)

def create_progress_modal_card(title: str, create_fn, modal_id: str):
    """Create a modal card"""
    return (
        fh.Card(
            fh.Header(fh.H3(title, cls="text-xl font-bold mb-4 text-primary-content")),
            create_fn(),
            cls="bg-base-200 shadow-lg rounded-lg"
        ),
        modal_id
    )

def create_measurement_input_section(label: str, name: str, width: str = "w-full", **input_props):
    """Create a form input section with label and input"""
    return fh.Div(
        fh.Label(label, cls="label text-primary-content"),
        fh.Input(
            type="number",
            name=name,
            cls=f"input input-bordered {width} bg-base-200 text-primary-content placeholder-slate-400",
            **input_props
        ),
        cls="form-control"
    )

def create_weight_form():
    """Create the weight input form"""
    return fh.Form(
        hx_post="/update_weight",
        hx_target="#weight-result",
        cls="space-y-4"
    )(
        create_measurement_input_section("Weight (lbs)","weight", min="0", step="0.1", placeholder="Enter your weight"),
        fh.Button(
            "Update Weight",
            type="submit",
            cls="btn btn-primary w-full"
        ),
        fh.Div(id="weight-result")
    )

def create_height_form():
    """Create the height input form"""
    return fh.Form(
        hx_post="/update_height",
        hx_target="#height-result",
        cls="space-y-4"
    )(
        fh.Div(
            fh.Label("Height", cls="label text-primary-content"),
            fh.Div(
                create_measurement_input_section("Feet", "height_feet", "w-24", "0", "9", "ft"),
                create_measurement_input_section("Inches", "height_inches", "w-24", "0", "11", "in"),
                cls="flex space-x-4"
            )
        ),
        fh.Button(
            "Update Height",
            type="submit",
            cls="btn btn-primary w-full"
        ),
        fh.Div(id="height-result")
    )

def create_goal_form():
    """Create the fitness goal form"""
    return fh.Form(
        hx_post="/update_goal",
        hx_target="#goal-result",
        cls="space-y-4"
    )(
        fh.Div(
            fh.Label("Fitness Goal", cls="label text-primary-content"),
            fh.Select(
                *[
                    fh.Option(goal.value.title(), value=goal.value)
                    for goal in Goals
                ],
                name="fitness_goal",
                cls="select select-bordered w-full bg-base-200 text-primary-content"
            ),
            cls="form-control"
        ),
        fh.Button(
            "Update Goal",
            type="submit",
            cls="btn btn-primary w-full"
        ),
        fh.Div(id="goal-result")
    )

def create_weight_plot(measurements: list[tuple[str, float]]):
    """Create the weight progress plot"""
    dates = [m[0].split("T")[0] for m in measurements]
    weights = [m[1] for m in measurements]
    
    plot_data = json.dumps([{
        "x": dates,
        "y": weights,
        "type": "scatter",
        "mode": "lines+markers",
        "name": "Weight",
        "line": {"color": "rgb(37, 99, 235)"},
        "marker": {"color": "rgb(37, 99, 235)"}
    }])

    plot_layout = json.dumps({
        "title": "Weight Progress Over Time",
        "xaxis": {
            "title": "Date",
            "tickangle": -45,
            "automargin": True,
            "gridcolor": "rgb(71, 85, 105)",
            "zerolinecolor": "rgb(71, 85, 105)"
        },
        "yaxis": {
            "title": "Weight (lbs)",
            "automargin": True,
            "gridcolor": "rgb(71, 85, 105)",
            "zerolinecolor": "rgb(71, 85, 105)"
        },
        "margin": {"t": 50, "b": 100},
        "height": 500,
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": "rgb(226, 232, 240)"}
    })
    
    return plot_data, plot_layout

def create_stats_grid(measurements: list[tuple[str, float]]):
    """Create a grid of statistics cards"""
    weights = [m[1] for m in measurements]
    current_weight = f"{weights[-1]:.1f} lbs" if weights else "No data"
    total_change = f"{(weights[-1] - weights[0]):.1f} lbs" if len(weights) > 1 else "No change"
    measurement_count = str(len(weights))

    return fh.Div(
        create_stats_card("Current Weight", current_weight),
        create_stats_card("Total Change", total_change),
        create_stats_card("Measurements", measurement_count),
        cls="grid grid-cols-3 gap-4"
    )

def create_stats_card(title: str, value: str):
    """Create a card displaying a statistic with title and value"""
    return fh.Card(
        fh.H5(title, cls="text-sm text-primary-content"),
        fh.P(
            value,
            cls="text-2xl font-bold text-secondary-content"
        ),
        cls="p-4 text-center bg-base-300"
    )

async def update_height(height_feet: int, height_inches: int):
    """Handle height update"""
    total_height = (height_feet * 12) + height_inches
    DB.execute(
        "UPDATE user_info SET height = ? WHERE id = 1",
        (total_height,)
    )
    return fh.P(
        "Height updated successfully!",
        cls="text-green-600 font-semibold text-center mt-4"
    )

async def update_goal(fitness_goal: str):
    """Handle goal update"""
    DB.execute(
        "UPDATE user_info SET goal = ? WHERE id = 1",
        (fitness_goal,)
    )
    return fh.P(
        "Goal updated successfully!",
        cls="text-green-600 font-semibold text-center mt-4"
    ) 

async def update_weight(weight: float):
    """Handle weight update"""
    DB.execute(
        "INSERT INTO measurements (datetime, weight) VALUES (?, ?)",
        (datetime.now().isoformat(), weight)
    )
    return fh.P(
        "Weight updated successfully!",
        cls="text-green-600 font-semibold text-center mt-4"
    )