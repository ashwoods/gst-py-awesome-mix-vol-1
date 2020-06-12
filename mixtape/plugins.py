import logging
import asyncio
from typing import Any, MutableMapping, Callable, Optional

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst  # type: ignore

from mixtape.spec import hookimpl
from mixtape.exceptions import PlayerPipelineError

logger = logging.getLogger(__name__)


class MixtapePlugin:
    """
    Mixtape plugin base clase
    """

    def __init__(self, player: Any):
        self.player = player

    @hookimpl
    def setup(self) -> None:
        pass

    @hookimpl
    def teardown(self) -> None:
        pass

    # -- default actions -- #

    @hookimpl
    def on_ready(self) -> None:
        pass

    @hookimpl
    def on_play(self) -> None:
        pass

    @hookimpl
    def on_pause(self) -> None:
        pass

    @hookimpl
    def on_stop(self) -> None:
        pass


class Logger(MixtapePlugin):
    """
    Mixtape logging plugin.
    Purpose is mostly to dogfood the plugin spec
    """

    def __init__(self, player: Any):
        super().__init__(player)
        self.logger: logging.Logger = logging.getLogger(f"{self.player.__module__}.self")

    @hookimpl
    def setup(self) -> None:
        self.logger.debug("%s: setup completed.", self.player)

    @hookimpl
    def teardown(self) -> None:
        self.logger.debug("%s: teardown completed.", self.player)

    # -- default actions -- #

    @hookimpl
    def on_ready(self) -> None:
        self.logger.debug("%s: ready.", self.player)

    @hookimpl
    def on_play(self) -> None:
        self.logger.debug("%s: playing.", self.player)

    @hookimpl
    def on_pause(self) -> None:
        self.logger.debug("%s: paused.", self.player)

    @hookimpl
    def on_stop(self) -> None:
        self.logger.debug("%s: stopped.", self.player)


class MessageHandler(MixtapePlugin):
    """
    Gst.Bus message handler.
    Default handling sets the player asyncio events enabling
    the asyncio Player interface on default actions.
    """

    def __init__(self, player: Any):
        super().__init__(player)
        self.bus: Gst.Bus = self.player.pipeline.get_bus()
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.pollfd: Any = None

    def handle(self) -> None:
        """
        Asyncio reader callback, called when a message is available on
        the bus.
        """
        msg = self.bus.pop()
        if msg:
            handler = self.handlers.get(msg.type, self.on_unhandled_msg)
            handler(self.bus, msg)

    @hookimpl
    def setup(self) -> None:
        self.loop = asyncio.get_running_loop()
        self.pollfd = self.bus.get_pollfd()
        self.loop.add_reader(self.pollfd.fd, self.handle)

    @hookimpl
    def teardown(self) -> None:
        if self.loop:
            self.loop.remove_reader(self.pollfd.fd)
        self.pollfd = None
        self.loop = None

    @property
    def handlers(self) -> MutableMapping[Gst.MessageType, Callable[[Gst.Bus, Gst.Message], None]]:
        """Returns default message handling mapping"""
        return {
            Gst.MessageType.ERROR: self.on_error,
            Gst.MessageType.EOS: self.on_eos,
            Gst.MessageType.STATE_CHANGED: self.on_state_changed,
        }

    def on_state_changed(self, bus: Gst.Bus, message: Gst.Message) -> None:
        """
        Handler for `state_changed` messages
        """
        old, new, _ = message.parse_state_changed()

        if message.src != self.player.pipeline:
            return
        logger.debug(
            "%s: state changed received from pipeline from %s to %s on %s",
            self.player,
            Gst.Element.state_get_name(old),
            Gst.Element.state_get_name(new),
            bus,
        )

        self.player.events.pick_state(new)

    def on_error(self, bus: Gst.Bus, message: Gst.Message) -> None:
        """
        Handler for `error` messages
        By default it will parse the error message,
        log to `error` and append to `self.errors`
        """
        err, debug = message.parse_error()
        self.player.events.error.set()
        logger.error(
            "Error received from element %s:%s on %s", message.src.get_name(), err.message, bus
        )
        if debug is not None:
            logger.error("Debugging information: %s", debug)
        # TODO: Cleanup on bus error message. self.player.teardown()
        raise PlayerPipelineError(err)

    def on_eos(self, bus: Gst.Bus, message: Gst.Message) -> None:
        """
        Handler for eos messages
        By default it sets the eos event
        """
        self.player.events.eos.set()
        logger.info("EOS message: %s received from pipeline on %s", message, bus)

    def on_unhandled_msg(self, bus: Gst.Bus, message: Gst.Message) -> None:
        """
        Handler for all other messages.
        By default will just log with `debug`
        """
        logger.debug("Unhandled msg: %s on %s", message.type, bus)
