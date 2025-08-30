# Using Loguru with FastAPI is trickier than expected, because uvicorn's own logging interferes with loguru's.
# Cf https://medium.com/1mgofficial/how-to-override-uvicorn-logger-in-fastapi-using-loguru-124133cdcd4e
# Cf  https://stackoverflow.com/questions/77515630/incorrect-method-name-in-python-logging-output-always-displays-loggingcallhan

import logging
import sys

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


def format_record(record):
    """Custom formatter that conditionally shows extra fields"""


    # Base format
    format_string = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level>"

    # Only add source_id if it exists
    source_id = record["extra"].get("source_id", None)
    if source_id:
        format_string += f" | <yellow>src:{source_id}</yellow>"

    # Add other conditional fields here if needed

    # Complete the format: inject message directly so its color tags are parsed
    # Escape braces in message to not interfere with own formatting
    # TODO: this can cause failures when html tags are present in the logged message. Figure out a better way to preserve color tags
    message = record["message"].replace("{", "{{").replace("}", "}}")
    format_string += (
        " | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - " + f"<level>{message}</level>"
    )

    return format_string + "\n{exception}"


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

        log = logger.bind(request_id="app")  # TODO: Actually make this functional at some point

        # Handle malformed log messages from third-party libraries
        try:
            message = record.getMessage()
        except (TypeError, ValueError) as e:
            # Fallback for broken log formatting (like newspaper's %d with list)
            message = f"[MALFORMED LOG] {record.msg} (args: {record.args}) - Error: {e}"

        # Filter traceback to only show app code for exceptions (if enabled)
        # TODO: Figure out why stack traces are sometimes excessive
        if settings.FILTER_LIBRARY_TRACEBACKS and record.exc_info:
            filtered_exc_info = filter_app_traceback(record.exc_info)
        else:
            filtered_exc_info = record.exc_info
        log.opt(depth=depth, exception=filtered_exc_info).log(level, message)


def create_logger():
    logger.remove()
    logger.add(
        sys.stdout,
        enqueue=True,
        backtrace=True,
        colorize=True,
        diagnose=True,
        level="INFO",
        format=format_record,  # Use our custom format function
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

    return logger
