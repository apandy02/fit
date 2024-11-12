# Fitness Trackers

This subdirectory contains the code for integrating with various fitness tracking devices and services.

## Structure

The following is the structure of the subdirectory:

- `__init__.py`
- `tracker.py`: Contains the abstract base class `FitnessTracker` that defines the interface all tracker implementations must follow
- Device-specific implementations (e.g. `whoop.py`): Concrete implementations of the `FitnessTracker` interface for specific devices/services
