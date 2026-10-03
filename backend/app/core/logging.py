import logging
import sys
from typing import Any, Dict


class StructuredFormatter(logging.Formatter):
    """
    Format logs cleanly for development and structured output for production.
    Ensures secrets are not accidentally exposed in logs.
    """
    SENSITIVE_KEYS = {"api_key", "api_secret", "password", "token", "admin_api_key"}

    def format(self, record: logging.LogRecord) -> str:
        # Basic masking of sensitive data in record attributes if any
        if hasattr(record, "args") and isinstance(record.args, dict):
            clean_args = {
                k: ("***" if k.lower() in self.SENSITIVE_KEYS else v)
                for k, v in record.args.items()
            }
            record.args = clean_args
        return super().format(record)


def setup_logging(debug: bool = True) -> None:
    log_level = logging.DEBUG if debug else logging.INFO
    log_format = (
        "[%(asctime)s] [%(levelname)s] [%(name)s] "
        "[req_id=%(request_id)s]: %(message)s"
        if "%(request_id)s" in logging.BASIC_FORMAT
        else "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter(log_format))

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    # Clear existing handlers
    root_logger.handlers = [handler]

    # Silence overly verbose external loggers
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


logger = logging.getLogger("claudinary")
