"""Structured (JSON-lines) logging for TripMate."""
import json
import logging
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent / "logs" / "tripmate.log"
_RESERVED = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED:
                data[key] = value
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False, default=str)


def setup_logging(log_file: Path = LOG_FILE) -> None:
    """Write INFO+ JSON logs to a file; show only warnings/errors on the console."""
    logger = logging.getLogger("tripmate")
    if logger.handlers:  # already configured
        return
    logger.setLevel(logging.INFO)
    logger.propagate = False
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(JsonFormatter())
    console = logging.StreamHandler()
    console.setLevel(logging.WARNING)
    console.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(file_handler)
    logger.addHandler(console)
