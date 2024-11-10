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
├── src
│   ├── fitness_trackers.py
```

- `src/fit/fitness_trackers.py`: Contains the base class and interfaces for fitness trackers.
- `src/fit/trackers.py`: Implementation of different tracker integrations.
- `src/fit/whoop.py`: Specific implementation for Whoop tracker API.
- `src/fit/utils/conversions.py`: Utility functions for data conversions.
- `pyproject.toml`: Project configuration and dependencies.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Virtual environment tool (Optional but recommended)

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/ai-fitness-copilot.git
   ```

2. **Navigate to the Project Directory**

   ```bash
   cd ai-fitness-copilot
   ```

4. **Install Dependencies**

   ```bash
   uv venv
   uv pip install .
   ```