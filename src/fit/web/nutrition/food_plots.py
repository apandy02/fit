import json


def base_bar(x, y, name, color, x_offset=0, show_legend=True):
    """Create a base bar trace"""
    return {
        "type": "bar",
        "x": [x],
        "y": [y],
        "name": name,
        "marker": {
            "color": color,
            "width": 1.0 
        },
        "hoverinfo": "y",
        "showlegend": show_legend, 
        "width": 0.25, 
        "offset": x_offset 
    }

def create_apex_donut(data_points: tuple[list, ...]):
    """Create an ApexCharts donut plot for daily view
    
    Args:
        data_points: Tuple of lists containing (consumed, goal) or (consumed, goal, burned) data
    """
    consumed = data_points[0][0] if data_points[0][0] is not None else 0
    goal = data_points[1][0] if data_points[1][0] is not None else 0
    
    consumed = float(consumed)
    goal = float(goal)
    
    percentage = (consumed / goal * 100) if goal > 0 else 0
    percentage = min(percentage, 100)  # Cap at 100%
    remaining = max(0, goal - consumed)  # Ensure remaining is not negative

    js_code = f"""
    // Create a unique initialization function for this specific chart
    (function() {{
        const chartId = "{{plot_id}}";
        const chartData = {{
            consumed: {consumed:.1f},
            remaining: {remaining:.1f}
        }};

        function initializeChart() {{
            const element = document.getElementById(chartId);
            if (!element || typeof ApexCharts === 'undefined') return;

            // Destroy existing chart if it exists
            const existingChart = document.querySelector(`#${{chartId}} .apexcharts-canvas`);
            if (existingChart) return;

            const options = {{
                series: [chartData.consumed, chartData.remaining],
                colors: ["rgb(34, 197, 94)", "rgb(239, 68, 68)"],
                chart: {{
                    height: 270,
                    width: "100%",
                    type: "donut",
                }},
                stroke: {{
                    colors: ["transparent"],
                    lineCap: "",
                }},
                plotOptions: {{
                    pie: {{
                        donut: {{
                            labels: {{
                                show: false,
                                name: {{
                                    show: true,
                                    fontFamily: "Inter, sans-serif",
                                    offsetY: 20,
                                }},
                                total: {{
                                    showAlways: true,
                                    show: true,
                                    label: "Total",
                                    fontFamily: "Inter, sans-serif",
                                    formatter: function (w) {{
                                        return w.globals.seriesTotals.reduce((a, b) => a + b, 0).toFixed(1)
                                    }},
                                }},
                                value: {{
                                    show: true,
                                    fontFamily: "Inter, sans-serif",
                                    offsetY: 20,
                                    formatter: function (value) {{
                                        return value.toFixed(1)
                                    }},
                                }},
                            }},
                            size: "75%",
                        }},
                    }},
                }},
                grid: {{
                    padding: {{
                        top: -2,
                        bottom: 20,
                    }},
                }},
                labels: ["Consumed", "Remaining"],
                dataLabels: {{
                    enabled: false,
                }},
                legend: {{
                    show: false
                }},
            }};

            const chart = new ApexCharts(element, options);
            chart.render();
        }}

        // Initialize on page load if the element exists
        if (document.readyState === "complete") {{
            initializeChart();
        }} else {{
            document.addEventListener("DOMContentLoaded", initializeChart);
        }}

        // Initialize after HTMX content swap
        document.body.addEventListener("htmx:afterSwap", function(evt) {{
            // Only initialize if our target element is in the swapped content
            if (evt.detail.target && evt.detail.target.contains(document.getElementById(chartId))) {{
                initializeChart();
            }}
        }});
    }})();
    """
    
    return json.dumps([]), json.dumps({"height": 300}), js_code

def create_plotly_bars(title: str, y_axis_title: str, data_points: tuple[list, ...]):
    """Create a Plotly bar plot for weekly view
    
    Args:
        title: Title of the plot
        y_axis_title: Y-axis label
        data_points: Tuple of lists containing (consumed, goal) or (consumed, goal, burned) data
    """
    has_burned = len(data_points) > 2 and data_points[2] is not None
    data = []
    days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    for i in range(len(data_points[0])):
        # Only show legend for the first day's bars
        show_legend = (i == 0)
        data.extend([
            base_bar(days[i], data_points[0][i], "Consumed", "rgb(37, 99, 235)", -0.2, show_legend),
            base_bar(days[i], data_points[1][i], "Consumption Goal", "rgb(96, 165, 250)", 0, show_legend)
        ])
        if has_burned:
            data.append(base_bar(days[i], data_points[2][i], "Burned", "rgb(239, 68, 68)", 0.2, show_legend))
    
    layout = {
        "showlegend": True,
        "legend": {"orientation": "h", "y": -0.2},
        "height": 300,
        "margin": {"t": 50, "b": 100},
        "paper_bgcolor": "rgba(0,0,0,0)", 
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": "rgb(226, 232, 240)"},
        "yaxis": {
            "title": y_axis_title,
            "gridcolor": "rgb(71, 85, 105)",  
            "zerolinecolor": "rgb(71, 85, 105)"
        },
        "xaxis": {
            "gridcolor": "rgb(71, 85, 105)",
            "zerolinecolor": "rgb(71, 85, 105)"
        },
        "bargap": 0.15, 
        "bargroupgap": 0 
    }
    
    return json.dumps(data), json.dumps(layout), "" 
