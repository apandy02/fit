# Fit

A comprehensive fitness assistant that combines LLM-powered nutrition analysis with fitness tracking. Leverage data from your fitness trackers along with LMP (language model programs) grounded in scientific literature to help you get (or stay) fit.

## Table of Contents
- [Overview](#overview)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
- [Technology Stack](#technology-stack)
  - [Core](#core)
  - [Frontend Plugins](#frontend-plugins)
  - [Development](#development)
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

## Getting Started

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
   uv sync
   ```
### Running the Application
(note: all the operations here are performed from the project root directory)

Start the web interface:
```bash
uv run src/fit/web/app.py
```

The above might take a few seconds to execute the first time, but it will work (hang in there)

The application will be available at `http://localhost:5001/login`


## Technology Stack

### Core
- Python 3.10+
- FastHTML + HTMX (web application frontend and backend)
- ell (language model programming + evals)
- Pydantic (data models and validation)
- SQLite (databases)

### Frontend Plugins
- TailwindCSS
- DaisyUI
- AmCharts
- Plotly

### Development Tools
- uv (dependency management, tool runner, build/package management)
- ruff (linting/formatting)
- isort (import linting/formatting)
- unittest (testing)
- coveragepy (test coverage)


### Testing
(note: all the operations here are performed from the project root directory)

Run the test suite:
```bash
uv run -m unittest discover -v
```

Run the test suite with coverage:
```bash
uv run -m coverage run -m unittest discover -v
```

Generate a coverage report:

```bash
uv run -m coverage html # for coverage report in html
```

```bash
uv run -m coverage report # for coverage report in terminal
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
2. Run linting: `uv run ruff check . --fix`
3. Follow the existing code structure and documentation patterns
4. Submit a pull request


## Builds and packaging [Work in progress]

