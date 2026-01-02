import datetime
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(session_name:str,
                 strategy_name:str,
                 log_console:bool=True):
    if not os.path.exists("./logs"):
        os.makedirs("./logs")

    # Create logger and setup formatter
    logger = logging.getLogger(session_name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s :: %(name)s :: [%(levelname)s] :: %(message)s"
    )

    # File handler setup
    file_handler = RotatingFileHandler(
        f"./logs/{strategy_name}__{datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")}.log",
        maxBytes=1024*1024*10,  # 10 MB
        backupCount=5           # up to 5 log files
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler setup
    if log_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    logger.info("Logger is created.")

    return logger