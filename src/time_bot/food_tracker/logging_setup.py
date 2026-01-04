import logging
from typing import Iterable

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def setup_logging(extra_loggers: Iterable[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    for logger_name in extra_loggers or []:
        logging.getLogger(logger_name).setLevel(logging.INFO)
