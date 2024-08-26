import datetime
import json
import logging
import os
import traceback

from dotenv import load_dotenv

load_dotenv()


def make_logger(log_name: str) -> logging.Logger:
    """Create and return a file-based logger."""

    logger = logging.getLogger(f"{log_name}_log")
    logger.setLevel(getattr(logging, os.environ["LOG_LEVEL"]))
    log_handler = logging.FileHandler(filename=f"{log_name}.log", mode="w", encoding="utf-8")
    log_handler.setLevel(getattr(logging, os.environ["LOG_LEVEL"]))
    logger.addHandler(log_handler)
    return logger


def debug(logger: logging.Logger, payload: dict, err: BaseException | None = None) -> None:
    payload["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    payload["level"] = "DEBUG"
    if err is not None:
        payload["err"] = repr(err)
        payload["traceback"] = traceback.format_exc()
    logger.debug(json.dumps(payload))


def info(logger: logging.Logger, payload: dict, err: BaseException | None = None) -> None:
    payload["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    payload["level"] = "INFO"
    if err is not None:
        payload["err"] = repr(err)
        payload["traceback"] = traceback.format_exc()
    logger.info(json.dumps(payload))


def warning(logger: logging.Logger, payload: dict, err: BaseException | None = None) -> None:
    payload["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    payload["level"] = "WARNING"
    if err is not None:
        payload["err"] = repr(err)
        payload["traceback"] = traceback.format_exc()
    logger.warning(json.dumps(payload))


def error(logger: logging.Logger, payload: dict, err: BaseException | None = None) -> None:
    payload["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    payload["level"] = "ERROR"
    if err is not None:
        payload["err"] = repr(err)
        payload["traceback"] = traceback.format_exc()
    logger.error(json.dumps(payload))


def critical(logger: logging.Logger, payload: dict, err: BaseException | None = None) -> None:
    payload["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    payload["level"] = "CRITICAL"
    if err is not None:
        payload["err"] = repr(err)
        payload["traceback"] = traceback.format_exc()
    logger.critical(json.dumps(payload))
