import json
from datetime import datetime

import fasthtml.common as fh

from fit.nutrition.data import Goals
from fit.web.common import DB, create_fab_menu, create_modal, page_outline


def create_weight_form():
    """Create the weight input form"""
    return fh.Form(
        hx_post="/update_weight",
        hx_target="#weight-result",
        cls="space-y-4"
    )(
        fh.Div(
            fh.Label("Weight (lbs)", cls="label text-primary-content"),
            fh.Input(
                type="number",
                name="weight",
                min="0",
                step="0.1",
                placeholder="Enter your weight",
                cls="input input-bordered w-full bg-base-200 text-primary-content placeholder-slate-400"
            ),
            cls="form-control"
        ),
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
                fh.Div(
                    fh.Label("Feet", cls="label text-primary-content"),
                    fh.Input(
                        type="number",
                        name="height_feet",
                        min="0",
                        max="9",
                        placeholder="ft",
                        cls="input input-bordered w-24 bg-base-200 text-primary-content placeholder-slate-400"
                    ),
                    cls="form-control"
                ),
                fh.Div(
                    fh.Label("Inches", cls="label text-primary-content"),
                    fh.Input(
                        type="number",
                        name="height_inches",
                        min="0",
                        max="11",
                        placeholder="in",
                        cls="input input-bordered w-24 bg-base-200 text-primary-content placeholder-slate-400"
                    ),
                    cls="form-control"
                ),
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

def create_weight_plot():
    """Create the weight progress plot"""
    measurements = DB.execute(
        "SELECT datetime, weight FROM measurements ORDER BY datetime"
    ).fetchall()
    
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

def create_stats_grid(weights):
    """Create the statistics grid"""
    return fh.Grid(
        fh.Card(
            fh.H5("Current Weight", cls="text-sm text-primary-content"),
            fh.P(
                f"{weights[-1]:.1f} lbs" if weights else "No data",
                cls="text-2xl font-bold text-secondary-content"
            ),
            cls="p-4 text-center bg-base-300"
        ),
        fh.Card(
            fh.H5("Total Change", cls="text-sm text-primary-content"),
            fh.P(
                f"{(weights[-1] - weights[0]):.1f} lbs" if len(weights) > 1 else "No change",
                cls="text-2xl font-bold text-secondary-content"
            ),
            cls="p-4 text-center bg-base-300"
        ),
        fh.Card(
            fh.H5("Measurements", cls="text-sm text-primary-content"),
            fh.P(
                str(len(weights)),
                cls="text-2xl font-bold text-secondary-content"
            ),
            cls="p-4 text-center bg-base-300"
        ),
        cols=3,
        cls="gap-4 mt-6"
    )

def get():
    """Return the progress tracking page content"""
    measurements = DB.execute(
        "SELECT datetime, weight FROM measurements ORDER BY datetime"
    ).fetchall()
    weights = [m[1] for m in measurements]
    
    plot_data, plot_layout = create_weight_plot()
    
    # Create FAB menu buttons
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
                # Plot container and script
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
                        create_stats_grid(weights),
                    ),
                    cls="mt-8"
                ),
                cls="bg-base-200 shadow-lg rounded-lg p-6"
            ),
            # Add FAB menu
            create_fab_menu(fab_buttons),
            # Add modals
            create_modal(
                fh.Card(
                    fh.Header(fh.H3("Update Weight", cls="text-xl font-bold mb-4 text-primary-content")),
                    create_weight_form(),
                    cls="bg-base-200 shadow-lg rounded-lg"
                ),
                "weight-modal"
            ),
            create_modal(
                fh.Card(
                    fh.Header(fh.H3("Update Height", cls="text-xl font-bold mb-4 text-primary-content")),
                    create_height_form(),
                    cls="bg-base-200 shadow-lg rounded-lg"
                ),
                "height-modal"
            ),
            create_modal(
                fh.Card(
                    fh.Header(fh.H3("Change Goal", cls="text-xl font-bold mb-4 text-primary-content")),
                    create_goal_form(),
                    cls="bg-base-200 shadow-lg rounded-lg"
                ),
                "goal-modal"
            ),
            cls="max-w-4xl mx-auto p-6 bg-base-100"
        ),
        cls="bg-base-100"
    )
    return page_outline(2, "Progress Tracking", content)

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