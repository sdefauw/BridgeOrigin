#!/usr/bin/env python
# coding: utf-8

import logging
import logging.handlers

import config

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

# The background is set with 40 plus the number of the color, and the foreground with 30

# These are the sequences need to get colored ouput
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"

level = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

verbose_levels = {
    0: "WARNING",
    1: "INFO",
    2: "DEBUG"
}


def formatter_message(message, use_color=True):
    if use_color:
        message = message.replace("$RESET", RESET_SEQ).replace("$BOLD", BOLD_SEQ)
    else:
        message = message.replace("$RESET", "").replace("$BOLD", "")
    return message


COLORS = {
    'WARNING': YELLOW,
    'INFO': GREEN,
    'DEBUG': BLUE,
    'CRITICAL': MAGENTA,
    'ERROR': RED
}


class ColoredFormatter(logging.Formatter):
    def __init__(self, msg, use_color=True):
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color

    def format(self, record):
        levelname = record.levelname
        if self.use_color and levelname in COLORS:
            levelname_color = COLOR_SEQ % (30 + COLORS[levelname]) + levelname + RESET_SEQ
            record.levelname = levelname_color
        return logging.Formatter.format(self, record)


# Custom logger class with multiple destinations
class ColoredLogger(logging.Logger):
    FORMAT = "%(levelname)-1s %(message)s"
    COLOR_FORMAT = formatter_message(FORMAT, True)

    def __init__(self, name):
        logging.Logger.__init__(self, name, logging.WARNING)

        color_formatter = ColoredFormatter(self.COLOR_FORMAT)

        console = logging.StreamHandler()
        console.setFormatter(color_formatter)

        self.addHandler(console)
        return


def init(verbosity):
    v_level = 0 if verbosity < 0 else 2 if verbosity > 2 else verbosity
    config.log_level = verbose_levels[v_level]
    LOG_FILENAME = config.config['server']['log']
    if LOG_FILENAME:
        LOG_SIZE = 2 * 1024 * 1024  # 2MB
        fh = logging.handlers.RotatingFileHandler(
                LOG_FILENAME, maxBytes=LOG_SIZE, backupCount=5)
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s %(levelno)s "
                                      "%(message)s")
        fh.setFormatter(formatter)

        logging.getLogger('').addHandler(fh)

    logger.setLevel(level[config.log_level])


logging.setLoggerClass(ColoredLogger)
logger = logging.getLogger("WebUI")

# Use approach of Pika, allows for log.debug("message")
debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error
critical = logger.critical

loggerRoot = logging.getLogger("")
loggerRoot.setLevel(logging.INFO)
