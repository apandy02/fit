"""
Contains the errors that are raised by the nutrition module.
"""

class NoMealsLoggedError(Exception):
    """Exception raised for when no meals are logged for a day."""
    def __init__(self, message="No meals logged for today, please log your meals and try again."):
        self.message = message
        super().__init__(self.message)
