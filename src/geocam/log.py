"""

Log module for geocam.

"""
import logging
import os
import sys
import platform


class CustomFormatter(logging.Formatter):
    def __init__(self, fmt, fmt_INFO):
        """

        Override to format the std log output such that INFO logs provide
        just the log message and other levels also provide the level type.

        Parameters
        ----------
        fmt : str
            Format of general log message.
        fmt_INFO : str
            Modified format of logging.INFO message.


        """
        super().__init__()
        self.fmt = fmt
        self.fmt_INFO = fmt_INFO

        # Colours.
        self.white = "\u001b[37m"
        self.yellow = "\x1b[38;5;226m"
        self.red = "\x1b[38;5;196m"
        self.bold_red = "\x1b[31;1m"
        self.reset = "\x1b[0m"

        # Format.
        self.FORMATS = {
            logging.DEBUG: self.white + self.fmt + self.reset,
            logging.INFO: self.white + self.fmt_INFO + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset,
        }

    def format(self, record):
        """

        Override to provide a custom log format.

        Parameters
        ----------
        record: LogRecord
            Log record object.

        """
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def initialise(level):
    """

    Function to initialise the log file.

    Parameters
    ----------
    level : logging.level
        Log level. Options include: logging.VERBOSE, logging.DEBUG, logging.INFO,
        logging.WARNING, logging.ERROR and logging.FATAL. Defaults to logging.INFO.

    """
    # Get platform and define destination for the logging file.
    operating_system = platform.system()
    home_dir = os.path.expanduser("~")
    if operating_system == "Windows":
        log_dir = os.path.abspath(os.path.join(home_dir, "AppData/geocam"))
        isdir = os.path.isdir(log_dir)
        if isdir is False:
            os.mkdir(log_dir)
        log_file = os.path.abspath(os.path.join(home_dir, "AppData/geocam/geocam.log"))
    elif operating_system == "Linux":
        log_dir = os.path.abspath(os.path.join(home_dir, ".geocam"))
        isdir = os.path.isdir(log_dir)
        if isdir is False:
            os.mkdir(log_dir)
        log_file = os.path.abspath(os.path.join(home_dir, ".geocam/geocam.log"))

    # Delete log file if already in existence.
    if os.path.exists(log_file):
        os.remove(log_file)

    # Log format.
    format = "%(levelname)s - " "%(name)s - " "%(funcName)s - " "%(message)s"

    # INFO log format for console output.
    format_INFO = "%(message)s"

    # Basic configuration.
    logging.getLogger(__name__)

    # Output full log.
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(format))
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(CustomFormatter(format, format_INFO))
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(fh)
    root.addHandler(ch)

    return


def set_level(level):
    """

    Function to set the log level after initialisation.

    Parameters
    ----------
    level : logging.level
        Log level. Options include logging.VERBOSE, logging.DEBUG, logging.INFO,
        logging.WARNING, logging.ERROR and logging.FATAL. Defaults to logging.INFO.

    """
    log = logging.getLogger(__name__)
    log.setLevel(level)
