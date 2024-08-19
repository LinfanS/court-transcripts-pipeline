import logging

logger = logging.getLogger(__name__)


def square(x):
    logger.warning(f"Calculating square of {x}")
    return x * x


if __name__ == "__main__":

    print(square(5))
