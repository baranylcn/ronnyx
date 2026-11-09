import logging
from unittest.mock import patch

from uvicorn.logging import DefaultFormatter

from ronnyx import serve


def test_configure_logging_adds_one_formatted_handler():
    logger = logging.getLogger(serve.LOGGER_NAME)
    original_handlers = logger.handlers[:]
    original_level = logger.level
    original_propagate = logger.propagate

    try:
        logger.handlers.clear()
        logger.setLevel(logging.NOTSET)
        logger.propagate = True

        serve.configure_logging()
        serve.configure_logging()

        assert logger.level == logging.INFO
        assert logger.propagate is False
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0].formatter, DefaultFormatter)
    finally:
        logger.handlers[:] = original_handlers
        logger.setLevel(original_level)
        logger.propagate = original_propagate


@patch("ronnyx.serve.uvicorn.run")
def test_main_configures_logging_before_starting_server(run_mock):
    with patch("ronnyx.serve.configure_logging") as configure_mock:
        serve.main([])

    configure_mock.assert_called_once_with()
    run_mock.assert_called_once_with(
        "ronnyx.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )


@patch("ronnyx.serve.uvicorn.run")
def test_main_uses_host_and_port_options(run_mock):
    with patch("ronnyx.serve.configure_logging"):
        serve.main(["--host", "192.168.1.10", "--port", "9000"])

    run_mock.assert_called_once_with(
        "ronnyx.main:app",
        host="192.168.1.10",
        port=9000,
        reload=False,
    )
