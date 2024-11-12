# Fitness Trackers

This subdirectory contains the code for integrating with various fitness tracking devices and services.

## Structure

The following is the structure of the subdirectory:

- `__init__.py`
- `tracker.py`: Contains the abstract base class `FitnessTracker` that defines the interface all tracker implementations must follow
- Device-specific implementations (e.g. `whoop.py`): Concrete implementations of the `FitnessTracker` interface for specific devices/services


## Example Usage

### Connecting to Whoop

```python
from fit.trackers.whoop import Whoop

# Initialize Whoop tracker with credentials
whoop = Whoop(
    username="your_email@example.com",
    password="your_password"
)

# Get current resting heart rate
heart_rate = whoop.resting_heart_rate()
print(f"Current resting heart rate: {heart_rate} bpm")

# Get calories burned
calories = whoop.calories_burned()
print(f"Calories burned today: {calories} kcal")

# Get detailed recovery information
current_cycle = whoop._get_current_cycle()
cycle_id = current_cycle["id"]
recovery_data = whoop.get_recovery(cycle_id)
print(f"Recovery score: {recovery_data['score']}")
```

Note: Replace `your_email@example.com` and `your_password` with your actual Whoop credentials.