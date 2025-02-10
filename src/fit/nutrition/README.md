# Nutrition Module

This directory contains the core nutrition tracking and analysis functionality for the fitness assistant.

## Key Features

- Natural language food logging
- Image-based food recognition
- Macro and micronutrient tracking
- Personalized nutrition feedback
- Meal recommendations
- Goal based target calculation

## Implementation Details

The module is structured around several key components:

- `data.py`: Core data models for nutrition tracking
- `targets.py`: Calculation of nutritional targets
- `assistants.py`: LLM-powered analysis and recommendations

The system uses structured prompts and response formats to ensure consistent and accurate nutrition tracking. All nutritional data is validated against predefined models using Pydantic.
