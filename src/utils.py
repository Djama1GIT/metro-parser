import time

from .logger import logger


def retry(tries=-1, delay=0, exceptions=Exception, log=False):
    def retry_decorator(func):
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
