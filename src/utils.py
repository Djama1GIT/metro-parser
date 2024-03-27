import time
from functools import wraps

from .logger import logger


def retry(tries=-1, delay=0, exceptions=Exception, log=False):
    """
    A decorator to retry a function or method in case of specified exceptions.

    This decorator allows a function or method to be retried a specified number of times
    if it raises any of the specified exceptions. It includes options for delaying retries,
    specifying which exceptions should trigger a retry, and logging retry attempts.

    Args:
        tries (int, optional): The maximum number of attempts. Defaults to -1, which means infinite retries.
        delay (int, optional): Delay between attempts in seconds. Defaults to 0, which means no delay.
        exceptions (Exception, optional): The type of exceptions that should trigger a retry.
        Defaults to Exception, which means all exceptions.
        log (bool, optional): Whether to log retry attempts. Defaults to False.

    Returns:
        A decorator that wraps the function or method to be retried.

    Example:
        @retry(tries=3, delay=2, exceptions=(ValueError,), log=True)
        def my_function():
            # Function body that may raise ValueError
            pass

    This example will retry `my_function` up to 3 times, with a 2-second delay between attempts,
    only if a ValueError is raised, and it will log each retry attempt.
    """
    def retry_decorator(func):
        @wraps(func)
        def retry_wrapper(*args, **kwargs):
            nonlocal tries, delay, exceptions
            while tries:
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    tries -= 1

                    if not tries:
                        raise exc

                    if log:
                        logger.error(f"Exception raised in {func.__name__}. Retrying... Exception: {str(exc)}")

                    time.sleep(delay)

        return retry_wrapper

    return retry_decorator
