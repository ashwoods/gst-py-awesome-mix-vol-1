import pluggy

hookimpl = pluggy.HookimplMarker("mixtape")
hookspec = pluggy.HookspecMarker("mixtape")


class PlayerSpec:
    """
    Player pluggy hook spec
    """

    @hookspec
    def setup(self) -> None:
        """
        This hook is used on player setup
        In a asyncio player it will be called
        from a thread with a running loop.
        """

    @hookspec
    def teardown(self) -> None:
        """
        This hook is used on player teardown,
        In a asyncio player it will be called
        from a thread with a running loop.
        """

    # -- default actions -- #

    @hookspec
    def on_ready(self) -> None:
        pass

    @hookspec
    def on_play(self) -> None:
        pass

    @hookspec
    def on_pause(self) -> None:
        pass

    @hookspec
    def on_stop(self) -> None:
        pass
