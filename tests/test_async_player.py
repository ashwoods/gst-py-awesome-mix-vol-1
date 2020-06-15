# type: ignore
import asyncio
import pytest

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst

from mixtape import Player
from mixtape.exceptions import PlayerSetStateError

SIMPLE_PIPELINE_DESCRIPTION = """videotestsrc ! queue ! fakesink"""
ERROR_PIPELINE_DESCRIPTION = "filesrc ! queue ! fakesink"


@pytest.fixture
def pipeline(Gst):
    """Make sure test pipeline is correct and test env setup"""
    pipeline = Gst.parse_launch(SIMPLE_PIPELINE_DESCRIPTION)
    assert isinstance(pipeline, Gst.Pipeline)
    return pipeline


@pytest.mark.parametrize(
    "method, state",
    [
        ("ready", Gst.State.READY),
        ("play", Gst.State.PLAYING),
        ("pause", Gst.State.PAUSED),
        ("stop", Gst.State.NULL),
    ],
)
@pytest.mark.asyncio
async def test_player_async_methods(pipeline, mocker, method, state):
    player = Player(pipeline)
    player.setup()
    spy = mocker.spy(player.pipeline, "set_state")

    action = getattr(player, method)

    try:
        await asyncio.wait_for(action(), 1)
    except Exception:
        # in this test we just care that set_state is being called correctly
        pass
    spy.assert_called_with(state)
    player.teardown()


@pytest.mark.asyncio
async def test_async_player_exception(Gst):
    """
    If we get a direct error from Gst.pipeline.set_state
    an exception should be returned inmediately
    """
    pipeline = Gst.parse_launch(ERROR_PIPELINE_DESCRIPTION)
    player = Player(pipeline)
    player.setup()

    with pytest.raises(PlayerSetStateError):
        await player.play()
    player.teardown()


@pytest.mark.asyncio
async def test_async_player_sequence(Gst, pipeline):
    """
    If we get a direct error from Gst.pipeline.set_state
    an exception should be returned inmediately
    """
    player = await Player.create(pipeline)

    sequence = ["ready", "play", "pause", "stop"]
    for step in sequence:
        await getattr(player, step)()
        await asyncio.sleep(1)
    player.teardown()


@pytest.mark.asyncio
async def test_player_properties(Gst, pipeline):
    player = await Player.create(pipeline)
    # TODO: test type
    assert len(list(player.sinks)) == 1
    assert len(list(player.sinks)) == 1
    assert len(list(player.elements)) == 3