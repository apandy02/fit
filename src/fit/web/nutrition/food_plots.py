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
            "width": 1.0  # Make bars thicker
        },
        "hoverinfo": "y",
        "showlegend": show_legend,  # Only show legend for first day's bars
        "width": 0.25,  # Control bar width
        "offset": x_offset  # Shift bars horizontally
    }

def create_amcharts_donut(title: str, y_axis_title: str, data_points: tuple[list, ...]):
    """Create an amCharts donut plot for daily view
    
    Args:
        title: Title of the plot
        y_axis_title: Y-axis label
        data_points: Tuple of lists containing (consumed, goal) or (consumed, goal, burned) data
    """
    consumed = data_points[0][0] if data_points[0][0] is not None else 0
    goal = data_points[1][0] if data_points[1][0] is not None else 0
    
    # Calculate percentages for the donut
    percentage = (consumed / goal * 100) if goal > 0 else 0
    percentage = min(percentage, 100)  # Cap at 100%
    remaining = goal - consumed
    
    # Create amCharts data
    data = [
        {
            "category": "Consumed",
            "value": percentage,
            "actualValue": consumed,
            "color": "rgb(37, 99, 235)",
            "legendValue": f"{consumed:.1f}"
        },
        {
            "category": "Remaining",
            "value": 100 - percentage,
            "actualValue": remaining,
            "color": "rgb(96, 165, 250)",
            "legendValue": f"{remaining:.1f}"
        }
    ]
    
    # Create the JavaScript to initialize the chart
    js_code = f"""
    // Create root element
    var root = am5.Root.new("{{plot_id}}");
    root.setThemes([am5themes_Dark.new(root)]);
    
    // Create chart
    var chart = root.container.children.push(am5percent.PieChart.new(root, {{
        layout: root.verticalLayout,
        innerRadius: am5.percent(75)
    }}));
    
    // Create series
    var series = chart.series.push(am5percent.PieSeries.new(root, {{
        valueField: "value",
        categoryField: "category",
        startAngle: 270,
        endAngle: 630
    }}));
    
    series.slices.template.setAll({{
        fillField: "color",
        stroke: am5.color(0x000000),
        strokeWidth: 2,
        tooltipText: "{{category}}: {{actualValue}}",
    }});
    
    series.labels.template.set("visible", false);  // Hide default labels
    
    // Set up custom legend labels
    series.labels.template.setAll({{
        text: "{{category}}: {{legendValue}}"
    }});
    
    series.data.setAll({json.dumps(data)});
    
    // Add legend with custom text
    var legend = chart.children.push(am5.Legend.new(root, {{
        centerX: am5.percent(50),
        x: am5.percent(50),
        marginTop: 15,
        marginBottom: 15,
        nameField: "category",
        valueField: "legendValue"
    }}));
    legend.data.setAll(series.dataItems);
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
        "bargap": 0.15,  # Gap between groups of bars
        "bargroupgap": 0  # No gap between bars in a group
    }
    
    return json.dumps(data), json.dumps(layout), ""  # Empty string for js_code since using Plotly
