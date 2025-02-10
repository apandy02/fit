# Fit

A comprehensive fitness assistant that combines LLM-powered nutrition analysis with fitness tracking. Leverage data from your fitness trackers along with LMP (language model programs) grounded in scientific literature to help you get (or stay) fit.

## Table of Contents
- [Overview](#overview)
- [Technology Stack](#technology-stack)
  - [Core](#core)
  - [Frontend Plugins](#frontend-plugins)
  - [Development](#development)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Contributing](#contributing)

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
- [UV](https://docs.astral.sh/uv/getting-started/installation/) for package management

### Setup

1. Get OpenAI API access. Follow instructions [here](https://platform.openai.com/docs/quickstart)

2. Install UV by following instructions [here](https://docs.astral.sh/uv/getting-started/installation/)

3. Clone the repository:
   ```bash
   git clone git@github.com:apandy02/fit.git
   cd fit
   ```

4. Create virtual environment and sync dependencies:
   ```bash
   uv venv
   uv sync
   ```
### Running the Application

Start the web interface:
```bash
uv run src/fit/web/app.py
```

The above might take a few seconds to execute the first time, but it will work (hang in there)

The application will be available at `http://localhost:5001`

### Testing

Run the test suite:
```bash
uv run -m unittest discover -v
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

1. Ensure all tests pass: `uv run -m unittest discover -v`
2. Run linting (isort and ruff). There are pre commit hooks that should auto-run when you commit. If these don't run, run the linters manually with:
   - `uv run isort .`
   - `uv run ruff check . --fix`
4. Follow the existing code structure and documentation patterns
5. Submit a pull request
