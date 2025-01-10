# Fit

A comprehensive fitness assistant that combines LLM-powered nutrition analysis with fitness tracking. Leverage data from your fitness trackers along with LMP (language model programs) grounded in scientific literature to help you get (or stay) fit.

## Overview

The application consists of several core modules:
- Web interface built with FastHTML and HTMX
- LLM-powered nutrition tracking and analysis
- Multi-tracker fitness data integration
- Progress and performance monitoring

## Technology Stack

### Core
- Python 3.10+
- FastHTML + HTMX
- ell
- Pydantic
- SQLite

### Frontend Plugins
- TailwindCSS
- DaisyUI
- AmCharts
- Plotly

### Development
- UV (Package Management)
- Ruff (Linting)
- Unittest (Testing)

## Getting Started

### Prerequisites
- Python 3.10 or higher
- [UV](https://docs.astral.sh/uv/getting-started/installation/) for package management

### Installation

1. Clone the repository:
```bash
git clone git@github.com:aryamanpandya99/fit.git
cd fit
```

2. Create and activate virtual environment:
```bash
uv venv
source .venv/bin/activate  # On Unix
.venv\Scripts\activate     # On Windows
```

3. Install dependencies:
```bash
uv pip install -e .
```

### Running the Application

Start the web interface:
```bash
python -m fit.web.app
```

The application will be available at `http://localhost:8000`

### Testing

Run the test suite:
```bash
python -m unittest discover -v
```

## Project Structure

```
src/fit/
├── nutrition/       # LLM-powered nutrition analysis
├── trackers/        # Fitness tracker integrations
├── utils/          # Shared utilities
└── web/            # Web interface and API
```

Each module contains its own README with detailed documentation.

## Contributing

1. Ensure all tests pass: `python -m unittest discover -v`
2. Run linting: `ruff check .`
3. Follow the existing code structure and documentation patterns
4. Submit a pull request
