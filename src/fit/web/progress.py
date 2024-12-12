import fasthtml.common as fh
from datetime import datetime
from fit.web.common import MEASUREMENTS_TABLE, page_outline

def get():
    """Return the progress tracking page content"""
    # Get weight data from measurements table
    # TODO: Fix this
    measurements = MEASUREMENTS_TABLE.execute(
        "SELECT datetime, weight FROM measurements ORDER BY datetime"
    ).fetchall()
    
    # Format data for plotting
    dates = [m["datetime"].split("T")[0] for m in measurements]  # Get just the date part
    weights = [m["weight"] for m in measurements]
    
    # Create the plot
    plot = fh.Plot(
        data=[
            {
                "x": dates,
                "y": weights,
                "type": "scatter",
                "mode": "lines+markers",
                "name": "Weight",
                "marker": {"color": "rgb(59, 130, 246)"},  # Blue color
                "line": {"color": "rgb(59, 130, 246)"}
            }
        ],
        layout={
            "title": "Weight Progress Over Time",
            "xaxis": {
                "title": "Date",
                "tickangle": -45,
                "automargin": True
            },
            "yaxis": {
                "title": "Weight (lbs)",
                "automargin": True
            },
            "margin": {"t": 50, "b": 100},  # Add margin for rotated x labels
            "height": 500,
            "width": "100%",
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "rgb(55, 65, 81)"}  # Gray text
        }
    )
    
    content = fh.Article(
        fh.Div(
            # Header section
            fh.Card(
                fh.Header(
                    fh.H3("Your Progress", cls="text-2xl font-bold text-center mb-2"),
                    fh.P(
                        "Track your weight changes over time",
                        cls="text-gray-600 text-center"
                    ),
                    cls="mb-6"
                ),
                # Plot section
                fh.Div(
                    plot,
                    cls="p-4 bg-white rounded-lg shadow-lg"
                ),
                # Stats section
                fh.Div(
                    fh.Div(
                        fh.H4("Statistics", cls="text-lg font-semibold mb-4"),
                        fh.Grid(
                            # Latest weight
                            fh.Card(
                                fh.H5("Current Weight", cls="text-sm text-gray-600"),
                                fh.P(
                                    f"{weights[-1]:.1f} lbs" if weights else "No data",
                                    cls="text-2xl font-bold text-blue-600"
                                ),
                                cls="p-4 text-center"
                            ),
                            # Weight change
                            fh.Card(
                                fh.H5("Total Change", cls="text-sm text-gray-600"),
                                fh.P(
                                    f"{(weights[-1] - weights[0]):.1f} lbs" if len(weights) > 1 else "No change",
                                    cls="text-2xl font-bold text-blue-600"
                                ),
                                cls="p-4 text-center"
                            ),
                            # Number of measurements
                            fh.Card(
                                fh.H5("Measurements", cls="text-sm text-gray-600"),
                                fh.P(
                                    str(len(weights)),
                                    cls="text-2xl font-bold text-blue-600"
                                ),
                                cls="p-4 text-center"
                            ),
                            cols=3,
                            cls="gap-4 mt-6"
                        )
                    ),
                    cls="mt-8"
                ),
                cls="bg-white shadow-lg rounded-lg p-6"
            ),
            cls="max-w-4xl mx-auto p-6"
        )
    )
    return page_outline(3, "Progress Tracking", content) 