from __future__ import annotations

from psychopy import core, event
from psychopy.hardware import keyboard

from . import Callable, P, Scene

__all__ = ["frames", "duration", "close_on", "hardware_keyboard", "event_mouse"]
MOUSE_TYPES = ("left", "middle", "right")


def frames(times: int) -> Callable[[Scene[P]], Scene[P]]:
    """Change `scene.timer`"""

    def wrapper(self: Scene):
        self.timer = lambda: len(self.data["frame_times"]) >= times
        return self

    return wrapper


def duration(duration: float) -> Callable[[Scene[P]], Scene[P]]:
    """Change `scene.timer`"""

    def wrapper(self: Scene):
        self.timer = lambda: (
            duration is not None
            and core.getTime() - self.data["frame_times"][0]
            >= duration - self.win.monitorFramePeriod / 2
        )
        return self

    return wrapper


def close_on(*types: str) -> Callable[[Scene[P]], Scene[P]]:
    """Add close listeners"""

    def wrapper(self: Scene):
        for k in types:
            self.on(k, self.close)
        return self

    return wrapper


class hardware_keyboard:
    """
    use `hardware.keyboard.Keyboard`
    :event-type key_any: press any key
    :event-type key_<name>: press special key, e.g., `key_space`
    :event-value key: `hardware.keyboard.KeyPress`
    """

    kb: keyboard.Keyboard

    def __init__(self, kb: keyboard.Keyboard | None = None):
        if kb is None:
            hardware_keyboard.kb = keyboard.Keyboard()
        else:
            self.kb = kb

    def poll(self, s: Scene):
        for key in self.kb.getKeys():
            s.emit(f"key_{key.value}", key).emit("key_any", key)

    def __call__(self, s: Scene[P]) -> Scene[P]:
        return s.on("show", lambda _: self.kb.clearEvents()).on(
            "poll", lambda _: self.poll(s)
        )


class event_mouse:
    """
    use `event.Mouse`
    :event-type mouse_any: press any mouse
    :event-type mouse_left: press left mouse
    :event-type mouse_middle:
    :event-type mouse_right:
    :event-value mouse: `{"name": str, "rt": float}`
    """

    mouse: event.Mouse

    def __init__(self, mouse: event.Mouse | None = None) -> None:
        if mouse is not None:
            self.mouse = mouse

    def poll(self, s: Scene):
        buttons, button_times = self.mouse.getPressed(getTime=True)
        for index, name in enumerate(MOUSE_TYPES):
            if buttons[index] == 1:  # pyright: ignore[reportIndexIssue]
                evt = { "name": name, "rt": button_times[index] }
                s.emit(f"mouse_{name}", evt).emit('mouse_any', evt)  # pyright: ignore[reportIndexIssue]

    def __call__(self, s: Scene[P]) -> Scene[P]:
        if not hasattr(self, "mouse"):
            event_mouse.mouse = event.Mouse(s.win)
        return s.on("show", lambda _: s.win.callOnFlip(self.mouse.clickReset)).on(
            "poll", lambda _: self.poll(s)
        )
