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
            "width": 0.8  # Make bars thicker
        },
        "hoverinfo": "y",
        "showlegend": show_legend,  # Only show legend for first day's bars
        "width": 0.2,  # Control bar width
        "offset": x_offset  # Shift bars horizontally
    }


def create_plot(title: str, y_axis_title: str, data_points: list[tuple]):
    """Create a plot with the provided data
    
    Args:
        title: Title of the plot
        y_axis_title: Y-axis label
        data_points: List of (consumed, goal) or (consumed, goal, burned) tuples
    """
    data = []
    has_burned = len(data_points[0]) == 3
    
    if len(data_points) == 1:
        # Single day plot
        consumed, goal = data_points[0][:2]
        data = [
            base_bar("Today", consumed, "Consumed", "rgb(37, 99, 235)"),
            base_bar("Today", goal, "Consumption Goal", "rgb(96, 165, 250)")
        ]
        if has_burned:
            data.append(base_bar("Today", data_points[0][2], "Burned", "rgb(239, 68, 68)"))
    else:
        # Weekly plot
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        
        # Add all bars for each day together
        for i, point in enumerate(data_points):
            # Only show legend for the first day's bars
            show_legend = (i == 0)
            data.extend([
                base_bar(days[i], point[0], "Consumed", "rgb(37, 99, 235)", -0.2, show_legend),
                base_bar(days[i], point[1], "Consumption Goal", "rgb(96, 165, 250)", 0, show_legend)
            ])
            if has_burned:
                data.append(base_bar(days[i], point[2], "Burned", "rgb(239, 68, 68)", 0.2, show_legend))
    
    layout = {
        "title": title,
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
        "bargap": 0.15,  # Gap between groups of bars
        "bargroupgap": 0  # No gap between bars in a group
    }
    
    return json.dumps(data), json.dumps(layout) 