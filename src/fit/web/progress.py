import json
from datetime import datetime

import fasthtml.common as fh

from fit.nutrition.data_models import Goals
from fit.web.common import DB, page_outline
from fit.web.databases import (get_latest_user_measurements,
                               get_user_measurements, insert_user_measurements)


def get():
    """Return the progress tracking page content"""
    measurements = get_user_measurements(DB)
    plot_data, plot_layout = create_weight_plot(measurements)
    
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
                        fh.H3("Statistics", cls="text-2xl font-semibold mb-4 text-primary-content text-center"),
                        create_stats_grid(measurements),
                    ),
                    cls="mt-8"
                ),
                cls="bg-base-200 shadow-lg rounded-lg p-6"
            ),
            fh.Div(
                fh.Button(
                    fh.Span("+", cls="text-2xl"),
                    cls="btn btn-circle btn-primary",
                    onclick="openMeasurementsModal()"
                ),
                cls="fixed bottom-8 right-8"
            ),
            measurements_modal(),
            cls="max-w-4xl mx-auto p-6 bg-base-100"
        ),
        cls="bg-base-100"
    )
    return page_outline(2, "Progress Tracking", content)

def get_latest_measurements():
    """Get the latest measurements from the database"""
    latest = get_latest_user_measurements(DB)
    
    if latest:
        weight = latest["weight"] if latest["weight"] is not None else 0
        height = latest["height"] if latest["height"] is not None else 0
        feet = height // 12 if height > 0 else 0
        inches = height % 12 if height > 0 else 0
    else:
        weight = 0
        feet = 0
        inches = 0
    
    return weight, feet, inches

def create_weight_form():
    """Create the weight input form"""
    weight, _, _ = get_latest_measurements()
    return fh.Form(
        hx_post="/update_weight",
        hx_target="#weight-result",
        cls="space-y-4"
    )(
        create_measurement_input_section("Weight (lbs)", "weight", min="0", step="0.1", placeholder="Enter your weight", value=str(weight)),
        fh.Button(
            "Update Weight",
            type="submit",
            cls="btn btn-primary w-full"
        ),
        fh.Div(id="weight-result")
    )

def create_height_form():
    """Create the height input form"""
    _, feet, inches = get_latest_measurements()
    return fh.Form(
        hx_post="/update_height",
        hx_target="#height-result",
        cls="space-y-4"
    )(
        fh.Div(
            fh.Label("Height", cls="label text-primary-content"),
            fh.Div(
                create_measurement_input_section("Feet", "height_feet", "w-24", step="1", min="0", max="9", placeholder="ft", value=str(feet)),
                create_measurement_input_section("Inches", "height_inches", "w-24", min="0", max="11", placeholder="in", value=str(inches)),
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
            cls="text-lg font-bold text-secondary-content"
        ),
        cls="p-4 text-center bg-base-300"
    ) 

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

def measurements_modal():
    """Create the measurements tracking modal"""
    weight, feet, inches = get_latest_measurements()
    return fh.Div(
        fh.Dialog(
            fh.Div(
                fh.Div(
                    fh.Button(
                        "×",
                        cls="absolute right-4 top-4 text-xl font-light text-primary-content hover:text-primary-content focus:outline-none focus:ring-0 border-none outline-none",
                        onclick="closeMeasurementsModal()",
                        style="outline: none; box-shadow: none;"
                    ),
                    fh.H3("Update Measurements", cls="text-xl font-bold text-center mt-4 mb-8 text-primary-content"),
                    fh.Form(
                        hx_post="/update_measurements",
                        hx_target="#measurements-result",
                        cls="w-[90%] mx-auto space-y-6"
                    )(
                        fh.Div(
                            fh.Label("Weight (lbs)", cls="label text-primary-content"),
                            fh.Input(
                                type="number",
                                name="weight",
                                step="0.1",
                                min="0",
                                required=True,
                                placeholder="Enter your weight",
                                value=str(weight),
                                cls="input input-bordered w-full bg-base-200 text-primary-content"
                            ),
                            cls="form-control"
                        ),
                        fh.Div(
                            fh.Label("Height", cls="label text-primary-content"),
                            fh.Div(
                                fh.Div(
                                    fh.Label("Feet", cls="label text-primary-content"),
                                    fh.Input(
                                        type="number",
                                        name="height_feet",
                                        step="1",
                                        min="0",
                                        max="9",
                                        placeholder="ft",
                                        value=str(feet),
                                        cls="input input-bordered w-full bg-base-200 text-primary-content"
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
                                        value=str(inches),
                                        cls="input input-bordered w-full bg-base-200 text-primary-content"
                                    ),
                                    cls="form-control"
                                ),
                                cls="grid grid-cols-2 gap-4"
                            ),
                            cls="form-control"
                        ),
                        fh.Button(
                            "Save Measurements",
                            type="submit",
                            cls="btn btn-primary w-full mt-6"
                        ),
                        fh.Div(id="measurements-result", cls="mt-4"),
                        cls="mx-8"
                    ),
                    cls="p-6"
                ),
                cls="bg-base-200 outline outline-1 outline-primary-content rounded-lg relative w-full"
            ),
            id="measurements-modal",
            cls="modal"
        ),
        fh.Script("""
            function openMeasurementsModal() {
                document.getElementById('measurements-modal').showModal();
            }
            
            function closeMeasurementsModal() {
                document.getElementById('measurements-modal').close();
            }
        """)
    )

async def update_measurements(request: fh.Request):
    """Handle measurements update"""
    # Insert weight measurement
    form = await request.form()
    weight = float(form["weight"])
    height_feet = float(form["height_feet"])
    height_inches = float(form["height_inches"])
    total_height = (height_feet * 12) + height_inches
    insert_user_measurements(
        database=DB,
        height=total_height,
        weight=weight,
        datetime=datetime.now()
    )

    return fh.Div(
        fh.P(
            "Measurements updated successfully!",
            cls="text-green-600 font-semibold text-center mt-4"
        ),
        fh.Script("""
            setTimeout(() => {
                closeMeasurementsModal();
                window.location.reload();
            }, 1000);
        """)
    ) 