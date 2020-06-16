from typing import Any, Optional, Type, TypeVar, Tuple, List

import attr
import pluggy

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst  # type: ignore

from .base import BasePlayer
from .events import PlayerEvents
from .plugins import MixtapePlugin, Logger, MessageHandler
from .spec import PlayerSpec


PlayerT = TypeVar("PlayerT", bound="Player")
MixtapePluginT = Type[MixtapePlugin]


@attr.s
class Player(BasePlayer):
    """
    An asyncio compatible player.
    Interfaces with the `Gst.Bus` with an asyncio file descriptor,
    which is used to set `asyncio.Event` when received for the bus,
    allowing for asyncio compatible methods.
    """

    PLUGIN_SPEC: Any = PlayerSpec
    DEFAULT_PLUGINS: List[MixtapePluginT] = [Logger]
    REQUIRED_PLUGINS: List[MixtapePluginT] = [MessageHandler]

    plugins: Type[pluggy.PluginManager] = attr.ib(init=False, repr=False)
    events: PlayerEvents = attr.ib(init=False, default=attr.Factory(PlayerEvents))

    @plugins.default
    def _plugins(self) -> Type[pluggy.PluginManager]:
        pm = pluggy.PluginManager("mixtape")
        pm.add_hookspecs(self.PLUGIN_SPEC)
        return pm

    @property
    def hook(self) -> Any:
        """Convenience shortcut for pm hook"""
        return self.plugins.hook

    @property
    def sinks(self) -> List[Any]:
        """Returns all sink elements"""
        return list(self.pipeline.iterate_sinks())

    @property
    def sources(self) -> List[Any]:
        """Return all source elements"""
        return list(self.pipeline.iterate_sources())

    @property
    def elements(self) -> List[Any]:
        """Return all pipeline elements"""
        return list(self.pipeline.iterate_elements())

    def get_elements_by_gtype(self, gtype: Any) -> List[Any]:
        """Return all elements in pipeline that match gtype"""
        return [e for e in self.elements if e.get_factory().get_element_type() == gtype]

    # -- pipeline control -- #

    async def ready(self) -> Tuple[Gst.StateChangeReturn, Gst.State, Gst.State]:
        """Async override of base.ready"""
        ret = super()._ready()
        await self.events.wait_for_state(Gst.State.READY)
        self.hook.on_ready()
        return ret

    async def play(self) -> Tuple[Gst.StateChangeReturn, Gst.State, Gst.State]:
        """Async override of base.play"""
        ret = super()._play()
        await self.events.wait_for_state(Gst.State.PLAYING)
        self.hook.on_play()
        return ret

    async def pause(self) -> Tuple[Gst.StateChangeReturn, Gst.State, Gst.State]:
        """Async override of base.pause"""
        ret = super()._pause()
        await self.events.wait_for_state(Gst.State.PAUSED)
        self.hook.on_pause()
        return ret

    async def stop(self) -> Tuple[Gst.StateChangeReturn, Gst.State, Gst.State]:
        """Async override of base.stop"""
        ret = self.set_state(Gst.State.NULL)
        self.hook.on_stop()
        return ret

    async def send_eos(self) -> bool:
        """Send eos to pipeline and await event"""
        ret = self.pipeline.send_event(Gst.Event.new_eos())
        await self.events.eos.wait()
        self.hook.on_eos()
        return ret

    # -- setup and teaddown -- #

    def setup(self) -> None:
        """Setup needs a running asyncio loop"""
        self.hook.setup()
        super().setup()
        self.events.setup.set()

    def teardown(self) -> None:
        """Cleanup player references to loop and gst resources"""
        self.hook.teardown()
        super().teardown()
        self.events.teardown.set()

    # -- class factories -- #

    @classmethod
    async def create(
        cls: Type[PlayerT], pipeline: Gst.Pipeline, plugins: Optional[List[MixtapePluginT]] = None
    ) -> PlayerT:
        """Player factory from a given pipeline that calls setup by default"""
        player = cls(pipeline)
        if plugins is None:
            plugins = cls.REQUIRED_PLUGINS + cls.DEFAULT_PLUGINS
        for plugin in plugins:
            player.plugins.register(plugin(player))
        player.setup()
        return player

    @classmethod
    async def from_description(
        cls: Type[PlayerT], description: str, plugins: Optional[List[MixtapePluginT]] = None
    ) -> PlayerT:
        """Player factory from a pipeline description"""
        pipeline = Gst.parse_launch(description)
        assert isinstance(pipeline, Gst.Pipeline)
        return await cls.create(pipeline=pipeline, plugins=plugins)
