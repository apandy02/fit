# Performance Module

This directory contains the core performance and activity tracking functionality for the fitness assistant.

## Key Features

- Heart rate monitoring and analysis
- Step counting and activity tracking
- Calorie burn calculation
- Performance trend analysis
- Workout recommendations
- Activity goal setting and tracking

## Implementation Details

The module is structured around several key components:

- `data_models.py`: Core data models for performance tracking
- `assistants.py`: LLM-powered analysis and recommendations

The system uses structured prompts and response formats to provide personalized performance insights and recommendations. All performance data is validated against predefined models using Pydantic.
