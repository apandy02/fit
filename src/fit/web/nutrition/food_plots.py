import json


def base_bar(x, y, name, color):
    return {
        "type": "bar",
        "x": [x],
        "y": [y],
        "name": name,
        "marker": {"color": color},
        "hoverinfo": "y",
        "showlegend": True
    }

def create_plot(title: str, y_axis_title: str, consumed: float, goal: float, burned: float = None):
    """Create a plot with the provided data"""
    data = [
        base_bar("Today", consumed, "Consumed", "rgb(37, 99, 235)"),
        base_bar("Today", goal, "Consumption Goal", "rgb(96, 165, 250)")
    ]
    if burned is not None:
        data.append(base_bar("Today", burned, "Burned", "rgb(239, 68, 68)"))
    
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
        "barmode": "group"
    }
    return json.dumps(data), json.dumps(layout) 