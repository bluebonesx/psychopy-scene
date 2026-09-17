from psychopy import core, event
from psychopy.hardware import keyboard

from . import Callable, P, Scene

__all__ = [
    "close_on",
    "duration",
    "event_mouse",
    "frames",
    "hardware_keyboard",
    "record_frames",
]
MOUSE_TYPES = ("left", "middle", "right")


def record_frames(s: Scene[P]) -> Scene[P]:
    """record all frame times to `scene.data['frame_times']`"""
    record = lambda t: s.data.setdefault("frame_times", []).append(t)
    return s.on("drawn", record).on("redraw", record)


def frames(n_frames: int) -> Callable[[Scene[P]], Scene[P]]:
    """Change `scene.timer`: close the scene after `n_frames` frames"""

    def wrapper(s: Scene):
        def timer() -> bool:
            s.data["n_frames"] += 1
            return s.data["n_frames"] >= n_frames

        s.timer = timer
        return s.on("drawn", lambda _: s.data.setdefault("n_frames", 0))

    return wrapper


def duration(duration: float) -> Callable[[Scene[P]], Scene[P]]:
    """Change `scene.timer`"""

    def wrapper(s: Scene):
        s.timer = lambda: (
            core.getTime() - s.data["start_time"]
            >= duration - s.win.monitorFramePeriod / 2
        )
        return s

    return wrapper


def close_on(*types: str) -> Callable[[Scene[P]], Scene[P]]:
    """Add close listeners"""

    def wrapper(s: Scene):
        for k in types:
            s.on(k, s.close)
        return s

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
        return s.on(
            "show",
            lambda _: self.kb.clearEvents(),
        ).on("redraw", lambda _: self.poll(s))


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
        buttons, button_times = self.mouse.getPressed(getTime=True)  # pyright: ignore[reportGeneralTypeIssues]
        for index, name in enumerate(MOUSE_TYPES):
            if buttons[index] == 1:  # pyright: ignore[reportIndexIssue]
                evt = {"name": name, "rt": button_times[index]}  # pyright: ignore[reportIndexIssue]
                s.emit(f"mouse_{name}", evt).emit("mouse_any", evt)

    def __call__(self, s: Scene[P]) -> Scene[P]:
        if not hasattr(self, "mouse"):
            event_mouse.mouse = event.Mouse(s.win)
        return s.on(
            "show",
            lambda _: s.win.callOnFlip(self.mouse.clickReset),
        ).on("redraw", lambda _: self.poll(s))
