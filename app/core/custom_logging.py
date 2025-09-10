# Using Loguru with FastAPI is trickier than expected, because uvicorn's own logging interferes with loguru's.
# Cf https://medium.com/1mgofficial/how-to-override-uvicorn-logger-in-fastapi-using-loguru-124133cdcd4e
# Cf  https://stackoverflow.com/questions/77515630/incorrect-method-name-in-python-logging-output-always-displays-loggingcallhan

import logging
import sys
from datetime import datetime, timezone
import pytz

from logtail import LogtailHandler
from loguru import logger

from app.core.config import settings


def filter_app_traceback(exc_info):
    """Filter traceback to only show frames from app code, not library code."""
    if exc_info is None:
        return None

    exc_type, exc_value, exc_traceback = exc_info
    app_frames = []

    # Walk through the traceback and keep only frames from our app
    tb = exc_traceback
    while tb is not None:
        frame = tb.tb_frame
        filename = frame.f_code.co_filename

        # Keep frame if it's from our app directory (contains 'app/' but not site-packages)
        if "app/" in filename and "site-packages" not in filename and ".venv" not in filename:
            app_frames.append(tb)

        tb = tb.tb_next

    # If we found app frames, reconstruct the traceback with only those
    if app_frames:
        # Create a new traceback chain with only app frames
        new_tb = None
        for frame in reversed(app_frames):
            if new_tb is None:
                new_tb = frame
            else:
                # This is a bit hacky but necessary to chain tracebacks
                frame.tb_next = new_tb
                new_tb = frame

        return (exc_type, exc_value, new_tb)

    # If no app frames found, return original
    return exc_info


class InterceptHandler(logging.Handler):
    loglevel_mapping = {
        50: "CRITICAL",
        40: "ERROR",
        30: "WARNING",
        20: "INFO",
        10: "DEBUG",
        0: "NOTSET",
    }

    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except AttributeError:
            level = self.loglevel_mapping[record.levelno]

        frame, depth = logging.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        try:
            message = record.getMessage()
        except (TypeError, ValueError) as e:
            # Fallback for malformed log messages from third-party libraries (like newspaper's %d with list)
            message = f"[MALFORMED LOG] {record.msg} (args: {record.args}) - Error: {e}"

        # Filter traceback to only show app code for exceptions (if enabled)
        if settings.FILTER_LIBRARY_TRACEBACKS and record.exc_info:
            filtered_exc_info = filter_app_traceback(record.exc_info)
        else:
            filtered_exc_info = record.exc_info
        logger.opt(depth=depth, exception=filtered_exc_info).log(level, message)


class CustomLogtailHandler(LogtailHandler):
    """Custom Handler to display local German time without microseconds in its own column on logtail"""
    german_tz = pytz.timezone('Europe/Berlin')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def emit(self, record):
        local_dt = datetime.fromtimestamp(record.created, tz=self.german_tz).replace(microsecond=0)
        record.local_dt = local_dt
        super().emit(record)


def create_logger():
    logger.remove()

    # Add stdout logger
    logger.add(
        sys.stdout,
        enqueue=True,
        backtrace=True,
        colorize=True,
        diagnose=True,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    # Add logtail handler
    logtail_handler = CustomLogtailHandler(source_token=settings.LOGTAIL_TOKEN, host=settings.LOGTAIL_INGESTING_HOST)
    logger.add(
        logtail_handler,
        enqueue=True,
        backtrace=True,
        colorize=True,
        diagnose=True,
        level="INFO",
        format="<level>{message}</level>",
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0)
    for _log in ["uvicorn.access", "uvicorn", "uvicorn.error", "fastapi"]:
        _logger = logging.getLogger(_log)
        _logger.handlers = [InterceptHandler()]
        _logger.propagate = False

    # Eliminate spam from noisy third-party libraries
    logging.getLogger("asyncio").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)

    # Set loguru global singleton logger to colors=True so that color-tags are correctly interpreted within messages
    # cf https://github.com/Delgan/loguru/issues/80
    import loguru
    loguru.logger = logger.opt(colors=True)

    return logger
