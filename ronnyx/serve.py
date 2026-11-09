import argparse
import logging

import uvicorn
from uvicorn.logging import DefaultFormatter

LOGGER_NAME = "ronnyx"
# The API has no authentication and the agent acts with the configured
# credentials, so only expose it beyond localhost when asked to.
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def configure_logging() -> None:
    """Configure Ronnyx startup logs alongside Uvicorn's default output."""

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(DefaultFormatter("%(levelprefix)s %(message)s"))
    logger.addHandler(handler)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Ronnyx API server.")
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Interface to bind (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port to listen on (default: {DEFAULT_PORT})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None):
    args = parse_args(argv)
    configure_logging()
    uvicorn.run("ronnyx.main:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
