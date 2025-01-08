# Web Interface

This directory contains the code for the fitness assistant web interface implemented using FastHTML in Python.

## Stack Overview

- **FastHTML**: Python-based web framework, handles HTML generation, routing and request handling
- **TailwindCSS**, **DaisyUI**: For styling
- **AmCharts**, **Plotly**: For data visualization
- **SQLite**: For data persistence

## Key Features

- Nutrition tracking and analysis
- Performance monitoring
- Progress tracking
- Rest and recovery management
- User profile customization
- Real-time data visualization
- Responsive design

## Implementation Details

The application follows a modular structure where each major feature (nutrition, performance, etc.) is contained in its own directory. Each module typically contains:

- `requests.py`: Backend request handlers
- `ui.py`: Frontend components and layouts
- Supporting files for specific functionality

The UI is built using FastHTML components with HTMX for dynamic updates, minimizing the need for custom JavaScript. Data visualization is handled through AmCharts and Plotly libraries.

## Getting Started

1. Install dependencies:
```bash
pip install fasthtml htmx-python
```

2. Run the application:
```bash
python -m fit.web.app
```

by default the application will be available at `http://localhost:8000`
