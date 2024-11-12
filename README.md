# AI Fitness Copilot

AI Fitness Copilot is a comprehensive application designed to assist users in achieving their fitness goals by integrating data from various fitness trackers, allowing goal specification, and enabling calorie tracking through food images or natural language descriptions.

## Features

- **Multi-Tracker Support**: Connect and aggregate data from multiple fitness trackers such as Whoop, Fitbit, etc.
- **Personalized Goals**: Set and monitor personal fitness goals (weight loss, muscle gain, etc.).
- **Calorie Tracking**: Log meals using images of food or natural language descriptions to track calorie intake.

## Directory Structure

```
├── README.md
├── pyproject.toml
├── src
│   ├── __init__.py
│   ├── fit
│   │   ├── __init__.py
│   │   ├── fitness_trackers.py
│   │   ├── trackers.py
│   │   ├── whoop.py
│   │   └── utils
│   │       ├── __init__.py
│   │       └── conversions.py
│   └── nutrition
│       ├── __init__.py
│       ├── data.py
│       └── assistants.py
```

- `src/fit/trackers/`: Contains all fitness tracker related code, including base classes and specific implementations for different devices
- `src/fit/utils/`: Contains utility functions and helper methods used across the project
- `src/fit/nutrition/`: Contains the nutrition tracking and recommendation system powered by LLMs

## Getting Started

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/getting-started/installation/) for fast and easy package management

### Installation

1. **Clone the Repository**

   ```bash
   git clone git@github.com:aryamanpandya99/fit.git
   ```

2. **Navigate to the Project Directory**

   ```bash
   cd fit
   ```

4. **Install Dependencies**

   ```bash
   uv venv
   uv pip install .
   ```
