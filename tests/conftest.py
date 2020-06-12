# type: ignore
import logging
import colorlog
import pytest


def pytest_configure(config):
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "(%(asctime)s) [%(log_color)s%(levelname)s] | %(name)s | %(message)s [%(threadName)-10s]"
        )
    )

    # get root logger
    logger = logging.getLogger()
    logger.handlers = []
    logger.addHandler(handler)
    logger.setLevel(logging.WARN)
    logging.getLogger("mixtape").setLevel(logging.DEBUG)


@pytest.fixture
def Gst():  # noqa
    import gi

    gi.require_version("Gst", "1.0")
    from gi.repository import Gst as GstCls

    GstCls.init(None)
    return GstCls


@pytest.fixture
def player(Gst):
    from mixtape import Player

    return Player
