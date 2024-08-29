import loguru
import asyncio

logging = loguru.logger


class CancelledErrorFilter:
    def __call__(self, record):
        if record["exception"]:
            exc_type, _, _ = record["exception"]
            if exc_type is asyncio.exceptions.CancelledError:
                return False
        return True


# Apply the filter to the logger
logging.add(lambda msg: None, filter=CancelledErrorFilter())
