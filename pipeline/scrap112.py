import logging
from scrap113 import square


def initialise_logger() -> logging.Logger:
    """Initialise the logger to log to console."""
    logger = logging.getLogger("l_pipeline")
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger


def main():
    logger = initialise_logger()
    logger.info("This is a test log message")
    square(5)


if __name__ == "__main__":
    main()
