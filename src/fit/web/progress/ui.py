import json

import fasthtml.common as fh

from fit.nutrition.data_models import WeightGoal
from fit.web.common import page_outline


def create_progress_page(session, measurements: list[tuple[str, float]]):
    plot_data, plot_layout = create_weight_plot(measurements)
    print("measurements: ", measurements)
    content = fh.Article(
        fh.Div(
            fh.Card(
                fh.Header(
                    fh.H3("Your Progress", cls="text-2xl  text-center mb-2 text-base-content"),
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
                        fh.H3("Statistics", cls="text-2xl mb-4 text-base-content text-center"),
                        create_stats_grid(measurements),
                    ),
                    cls="mt-8"
                ),
                cls="bg-base-200 shadow-lg rounded-lg p-6"
            ),
            fh.Div(
                fh.Button(
                    fh.Span("+", cls="text-2xl"),
                    cls="btn btn-circle btn-neutral",
                    onclick="openMeasurementsModal()"
                ),
                cls="fixed bottom-8 right-8"
            ),
            measurements_modal(session["user_id"], measurements),
            cls="max-w-4xl mx-auto p-6 bg-base-100"
        ),
        cls="bg-base-100"
    )
    return page_outline(2, "Progress Tracking", True, True, content)

def create_weight_plot(measurements: list[tuple[str, float]]):
    """Create the weight progress plot"""

    dates = [m['datetime'] for m in measurements]
    weights = [m['weight'] for m in measurements]
    
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
    weights = [m['weight'] for m in measurements]
    print("weights: ", weights)
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
        fh.H5(title, cls="text-sm text-base-content"),
        fh.P(
            value,
            cls="text-lg  text-base-content"
        ),
        cls="p-4 text-center bg-base-300 shadow-none"
    ) 

def create_progress_modal_card(title: str, create_fn, modal_id: str):
    """Create a modal card"""
    return (
        fh.Card(
            fh.Header(fh.H3(title, cls="text-xl  mb-4 text-base-content")),
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
            fh.Label("Fitness Goal", cls="label text-base-content"),
            fh.Select(
                *[
                    fh.Option(goal.value.title(), value=goal.value)
                    for goal in WeightGoal
                ],
                name="fitness_goal",
                cls="select select-bordered w-full bg-base-200 text-base-content"
            ),
            cls="form-control"
        ),
        fh.Button(
            "Update Goal",
            type="submit",
            cls="btn btn-neutral w-full"
        ),
        fh.Div(id="goal-result")
    )

def measurements_modal(user_id: int, measurements: list[tuple[str, float, float]]):
    """Create the measurements tracking modal"""
    latest_measurement = measurements[0]
    return fh.Div(
        fh.Dialog(
            fh.Div(
                fh.Div(
                    fh.Button(
                        "×",
                        cls="absolute right-4 top-4 text-xl font-light text-base-content hover:text-base-content focus:outline-none focus:ring-0 border-none outline-none",
                        onclick="closeMeasurementsModal()",
                        style="outline: none; box-shadow: none;"
                    ),
                    fh.H3("Update Measurements", cls="text-xl  text-center mt-4 mb-8 text-base-content"),
                    fh.Form(
                        hx_post="/update_measurements",
                        hx_target="#measurements-result",
                        cls="w-[90%] mx-auto space-y-6"
                    )(
                        fh.Div(
                            fh.Label("Weight (lbs)", cls="label text-base-content"),
                            fh.Input(
                                type="number",
                                name="weight",
                                step="0.1",
                                min="0",
                                required=True,
                                placeholder="Enter your weight",
                                value=str(latest_measurement["weight"]),
                                cls="input input-bordered w-full bg-base-200 text-base-content"
                            ),
                            cls="form-control"
                        ),
                        fh.Div(
                            fh.Label("Height", cls="label text-base-content"),
                            fh.Div(
                                fh.Div(
                                    fh.Label("Feet", cls="label text-base-content"),
                                    fh.Input(
                                        type="number",
                                        name="height_feet",
                                        step="1",
                                        min="0",
                                        max="9",
                                        placeholder="ft",
                                        value=str(latest_measurement["height"] // 12),
                                        cls="input input-bordered w-full bg-base-200 text-base-content"
                                    ),
                                    cls="form-control"
                                ),
                                fh.Div(
                                    fh.Label("Inches", cls="label text-base-content"),
                                    fh.Input(
                                        type="number",
                                        name="height_inches",
                                        min="0",
                                        max="11",
                                        placeholder="in",
                                        value=str(latest_measurement["height"] % 12),
                                        cls="input input-bordered w-full bg-base-200 text-base-content"
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
                            cls="btn btn-neutral w-full mt-6"
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
