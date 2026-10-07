import logging
import os
import re


class CustomLoggingFormatter(logging.Formatter):
    """
    Provides some additional formatting for the logger, color-coding the output so that:
        'DEBUG' and 'INFO' messages are in gray
        'WARNING' messages are in yellow
        'ERROR' messages are in red
        'CRITICAL' messages are in green

    Modified from : https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
    """

    def __init__(self, color: bool = True) -> None:
        """Initialize instance of CustomLoggingFormatter class.

        Parameters
        ===========
        color: bool
            Setting to show color-coded results.
        """

        self.color = color

    def color_code(self, record) -> str:
        """
        Returns the color-coded and bolding format for a log record
        """

        if self.color:
            grey = "\x1b[38;20m"
            bold_grey = "\x1b[38;1m"
            yellow = "\x1b[33;20m"
            bold_yellow = "\x1b[33;1m"
            red = "\x1b[31;20m"
            bold_red = "\x1b[31;1m"
            green = "\x1b[32m"
            bold_green = "\x1b[1;32m"
            reset = "\x1b[0m"
            msg_format = "%(message)s"
        else:
            grey = "\x1b[20m"
            bold_grey = "\x1b[1m"
            yellow = "\x1b[20m"
            bold_yellow = "\x1b[1m"
            red = "\x1b[20m"
            bold_red = "\x1b[1m"
            green = "\x1b[20m"
            bold_green = "\x1b[1m"
            reset = "\x1b[0m"
            msg_format = "%(message)s"

        # Set color by log message level
        FORMATS = {
            logging.DEBUG: grey + msg_format + reset,
            logging.INFO: grey + msg_format + reset,
            logging.WARNING: yellow + msg_format + reset,
            logging.ERROR: red + msg_format + reset,
            logging.CRITICAL: bold_grey + msg_format + reset,
        }

        log_fmt = FORMATS.get(record.levelno)

        # Additional logic if specific strings are present in log message
        # Individual field and file verdicts
        if ": 'FAIL'" in record.msg:
            log_fmt = bold_red + msg_format + reset
        elif ": 'NEEDS REVIEW'" in record.msg:
            log_fmt = yellow + msg_format + reset
        elif ": 'PASS'" in record.msg:
            log_fmt = bold_green + msg_format + reset
        elif ": 'SKIPPED'" in record.msg:
            log_fmt = bold_yellow + msg_format + reset

        # Total score for file list
        if "All files passed!" in record.msg:
            log_fmt = green + msg_format + reset
        elif "Files Failed" in record.msg:
            n_failed = int(re.findall(r"Files Failed: (\d+)", record.msg)[0])
            print(n_failed)
            if n_failed > 0:  # make text red if any files failed
                log_fmt = bold_red + msg_format + reset

        if not log_fmt:
            log_fmt = grey + msg_format + reset
        return log_fmt

    def format(self, record) -> str:
        log_fmt = self.color_code(record)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logger(name: str, level: int = logging.INFO, color: bool = True) -> logging.Logger:
    """Create a custom logger."""

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(os.path.join(os.path.dirname(__file__), "../mct.log"))
    c_handler.setLevel(level)
    f_handler.setLevel(level)

    # Create formatters and add it to handlers
    c_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    f_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)
    # Color code the text for the terminal output
    c_handler.setFormatter(CustomLoggingFormatter(color))

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    return logger
