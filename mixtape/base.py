import logging
from typing import Tuple, TypeVar

import attr
import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst  # type: ignore

from .exceptions import PlayerSetStateError


logger = logging.getLogger(__name__)

BasePlayerType = TypeVar("BasePlayerType", bound="BasePlayer")


@attr.s
class BasePlayer:
    """Player base player"""

    pipeline: Gst.Pipeline = attr.ib()

    def __del__(self) -> None:
        """
        Make sure that the gstreamer pipeline is always cleaned up
        """
        if self.state is not Gst.State.NULL:
            logger.warning("Player cleanup on destructor")
            self.teardown()

    @property
    def state(self) -> Gst.State:
        """Convenience property for the current pipeline Gst.State"""
        return self.pipeline.get_state(0)[1]

    def set_state(self, state: Gst.State) -> Tuple[Gst.StateChangeReturn, Gst.State, Gst.State]:
        """Set pipeline state"""
        ret = self.pipeline.set_state(state)
        if ret == Gst.StateChangeReturn.FAILURE:
            raise PlayerSetStateError
        return ret

    def setup(self) -> None:
        """Player setup: meant to be used with hooks or subclassed"""

    def teardown(self) -> None:
        """Player teardown: by default sets the pipeline to Gst.State.NULL"""
        if self.state is not Gst.State.NULL:
            self.set_state(Gst.State.NULL)

    def _ready(self) -> Tuple[Gst.StateChangeReturn, Gst.State, Gst.State]:
        """Set pipeline to state to Gst.State.READY"""
        return self.set_state(Gst.State.READY)

    def _play(self) -> Tuple[Gst.StateChangeReturn, Gst.State, Gst.State]:
        """Set pipeline to state to Gst.State.PLAY"""
        return self.set_state(Gst.State.PLAYING)

    def _pause(self) -> Tuple[Gst.StateChangeReturn, Gst.State, Gst.State]:
        """Set pipeline to state to Gst.State.PAUSED"""
        return self.set_state(Gst.State.PAUSED)

    def _stop(self) -> Tuple[Gst.StateChangeReturn, Gst.State, Gst.State]:
        """Set pipeline to state to Gst.State.NULL"""
        return self.set_state(Gst.State.NULL)
