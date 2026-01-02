from dataclasses import asdict
import datetime
import logging
from logging.handlers import RotatingFileHandler
import os

from .data_models import MainConfig, StrategyConfig

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


def log_configs(logger, config:MainConfig):
    # Setup header line
    name_width=40
    value_width=40
    n_symbols_per_row = 5

    config_log_header = f"{'Config':^{name_width}} | {'Value':^{value_width}}"
    config_log_separator = f"{'-' * name_width}-+-{'-' * value_width}"

    # Initialize list of log lines
    log_lines = [config_log_header, config_log_separator]

    # Append each config value as a table row
    ## functions
    def flatten_dict(d, parent_key="", sep="."):
        items = {}
        for k, v in d.items():
            key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.update(flatten_dict(v, key, sep))
            else:
                items[key] = v
        return items

    def chunked(seq, size):
        for i in range(0, len(seq), size):
            yield seq[i:i + size]
    
    ## execute
    vars_to_log = flatten_dict(asdict(config))

    for name, value in vars_to_log.items():
        # For the "traded_assets" variable, display up to 5 symbols per table row
        if name == "traded_assets" and isinstance(value, list):
            chunks = list(chunked(value, n_symbols_per_row))

            for i, chunk in enumerate(chunks):
                symbols_str = ", ".join(chunk)

                row_name = name if i == 0 else ""
                log_lines.append(
                    f"{row_name:<{name_width}} | {symbols_str:>{value_width}}"
                )
        
        # All other config variables occupy one table row
        else:
            log_lines.append(f"{name:<40} | {str(value):>40}")

    # Log configuration
    logger.info("\n" + "\n".join(log_lines) + "\n\n")
