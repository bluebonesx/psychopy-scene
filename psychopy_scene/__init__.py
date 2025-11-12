from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Iterable, Protocol, cast

from psychopy import core, data, event, visual
from psychopy.hardware import keyboard
from typing_extensions import ParamSpec

P1 = ParamSpec("P1")
P2 = ParamSpec("P2")
__EVENT_RE = re.compile(
    r"scene_(setup|drawn|frame)|mouse_(left|middle|right)|key_(any|(num_)?(\d|[a-z]+))"
)
__MOUSE_BUTTONS = ["left", "middle", "right"]
Listener = Callable[[], Any]


@dataclass
class Event:
    value: str | keyboard.KeyPress
    rt: float


@dataclass
class EventEmitter:
    listeners: dict[str, Listener] = field(default_factory=dict)

    def on(self, type: str, listener: Listener):
        """add listener. Raise `ValueError` if already defined."""
        cb = self.listeners.get(type)
        if cb is not None:
            raise ValueError(f"{type} is already defined")
        if __EVENT_RE.fullmatch(type) is None:
            raise ValueError(f"{type} is not a valid listener name")
        self.listeners[type] = listener
        return self

    def off(self, type: str):
        """remove listener. Do nothing if not found."""
        self.listeners.pop(type, None)
        return self

    def emit(self, type: str):
        """emit listener. Do nothing if not found."""
        cb = self.listeners.get(type)
        if cb is not None:
            cb()
        return self


@dataclass
class DataCollector:
    data: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str):
        """get data. if value is `None`, raise `KeyError`.

        if you want to process `None` manually, use `self.data.get()` instead."""
        value = self.data.get(key)
        if value is None:
            raise KeyError(f"{key} is not in self.data")
        return value

    def set(self, key: str, value: Any):
        """set data"""
        self.data[key] = value
        return self


class Drawable(Protocol):
    def draw(self) -> Any: ...


class Scene(Generic[P1], DataCollector, EventEmitter):
    def __init__(self, env: "Context"):
        DataCollector.__init__(self)
        EventEmitter.__init__(self)
        self.win = env.win
        self.kbd = env.kbd
        self.mouse = env.mouse
        self.__shown = False
        self.duration: float | None = None
        self.drawables: Iterable[Drawable] = []
        self.config()

    def __call__(
        self, setup: Callable[P2, Drawable | Iterable[Drawable]]
    ) -> "Scene[P2]":
        return self.on("scene_setup", setup)  # type: ignore

    def config(
        self,
        duration: float | None = None,
        close_on: str | Iterable[str] | None = None,
        **listeners: Listener,
    ):
        """configure the scene

        :param duration: duration in seconds.
        :param close_on: event types.

        Example:
        >>> scene.config(duration=1, close_on="key_escape", on_key_space=lambda: print("space pressed"))
        """
        self.duration = duration
        if close_on:
            if isinstance(close_on, str):
                close_on = (close_on,)
            for k in close_on:
                self.on(k, self.close)
        for k, v in listeners.items():
            if not k.startswith("on_"):
                raise ValueError(f"{k} should start with 'on_'")
            self.on(k[3:], v)
        return self

    def draw(self):
        """draw all self.drawables"""
        for drawable in self.drawables:
            drawable.draw()
        return self

    def show(self, *args: P1.args, **kwargs: P1.kwargs):
        """show the scene with stimulus params"""
        if self.__shown:
            raise Exception(f"{self.__class__.__name__} has shown")
        self.__shown = True
        self.data = {}
        self.kbd.clearEvents()
        # emit on_scene_setup
        cb = self.listeners.get("scene_setup")
        if cb is None:
            raise Exception("on_scene_setup is not defined")
        results: Drawable | Iterable[Drawable] = cb(*args, **kwargs)
        self.drawables = results if isinstance(results, Iterable) else (results,)
        # reset clock
        self.kbd.clock.reset()
        self.mouse.clickReset()
        # first draw
        self.draw().win.flip()
        self.set("show_time", core.getTime())
        self.emit("scene_drawn")
        # capture interaction events
        events = []
        self.set("events", events)
        while self.__shown:
            # redraw
            self.emit("scene_frame")
            self.draw().win.flip()
            # listen to keyboard and mouse events
            buttons, button_times = cast(
                tuple[list[int], list[float]], self.mouse.getPressed(getTime=True)
            )
            for key in self.kbd.getKeys():
                events.append(Event(key, key.rt))
                self.emit(f"key_{key.value}")
                self.emit("key_any")
            for index, type in enumerate(__MOUSE_BUTTONS):
                if buttons[index] == 1:
                    events.append(Event(type, button_times[index]))
                    self.emit(f"mouse_{type}")
            if (
                self.duration is not None
                and core.getTime() - self.get("show_time")
                >= self.duration - self.win.monitorFramePeriod / 2
            ):
                self.close()
        return self

    def close(self):
        if not self.__shown:
            raise Exception(f"{self.__class__.__name__} has closed")
        self.__shown = False
        return self


@dataclass
class Context:
    win: visual.Window
    kbd: keyboard.Keyboard = field(default_factory=keyboard.Keyboard)
    mouse: event.Mouse = None  # type: ignore
    exp: data.ExperimentHandler = field(default_factory=data.ExperimentHandler)

    def __post_init__(self):
        self.mouse = self.mouse or event.Mouse(self.win)

    @property
    def scene(self):
        return Scene(self).config

    def text(self, *args, **kwargs):
        """create static text scene quickly"""
        stim = visual.TextStim(self.win, *args, **kwargs)
        return self.scene()(lambda: stim)

    def fixation(self, duration: float | None = None):
        return self.text("+").config(duration=duration)

    def blank(self, duration: float | None = None):
        return self.text("").config(duration=duration)

    def addRow(self, **kwargs: float | str | bool):
        for k, v in kwargs.items():
            self.exp.addData(k, v)
        self.exp.nextEntry()
