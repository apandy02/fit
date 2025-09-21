import json
import time
from functools import wraps
from typing import Type

from pydantic import BaseModel, ValidationError


def retry(model_class: Type[BaseModel], retries: int = 3, delay: float = 0.5):
    """
    A basic decorator that retries the function if Pydantic validation fails.
    Must be applied AFTER the ell.simple or ell.complex decorator.

    :param model_class: The Pydantic model class used to validate the function output
    :param retries: Maximum number of retries before giving up
    :param delay: Delay in seconds between retries
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(retries):
                try:
                    result = func(*args, **kwargs, error_context=str(last_exception))
                    model_class.model_validate(json.loads(result))
                    return result
                except ValidationError as validation_error:
                    last_exception = validation_error
                    if attempt < retries - 1:
                        time.sleep(delay)

            if last_exception is not None:
                raise last_exception

        return wrapper

    return decorator
