from __future__ import annotations

from dataclasses import dataclass, field
from functools import reduce
from typing import Any, Callable, Final, Generic, Iterable, Protocol

from psychopy import data, logging, visual
from typing_extensions import ParamSpec

__all__ = ["Listener", "EventEmitter", "Drawable", "Component", "Scene", "Context"]
P = ParamSpec("P")
Listener = Callable[[Any], Any]


class EventEmitter:
    def __init__(self) -> None:
        self.listeners: dict[str, set[Listener]] = {}

    def on(self, type: str, listener: Listener):
        listeners = self.listeners.get(type)
        if listeners is None:
            listeners = self.listeners[type] = set()
        listeners.add(listener)
        return self

    def off(self, type: str, listener: Listener):
        listeners = self.listeners.get(type)
        if listeners is not None:
            listeners.discard(listener)
            if not listeners:
                del self.listeners[type]
        return self

    def emit(self, type: str, evt: Any = None):
        listeners = self.listeners.get(type)
        if listeners:
            for listener in list(listeners):
                listener(evt)
        return self


class Drawable(Protocol):
    def draw(self) -> Any: ...


class Component(Protocol[P]):
    def __init__(self): ...
    def __call__(self, *a: P.args, **b: P.kwargs) -> Drawable | Iterable[Drawable]: ...


class Scene(Generic[P], EventEmitter):
    def __init__(self, win: visual.Window, comp: Component[P] | type[Component[P]]):
        EventEmitter.__init__(self)
        self.win = win
        self.shown = False
        self.drawables: Iterable[Drawable] = []
        self.data: Final[dict[str, Any]] = {}
        self.timer: Callable[[], bool] = lambda: False
        self.component: Component[P] = comp() if isinstance(comp, type) else comp
        setattr(self.component, "scene", self)
        for key in dir(self.component):
            if key.startswith("on_"):
                self.on(key[3:], getattr(self.component, key))

    def use(self, *decorators: Callable[[Scene[P]], Scene[P]]):
        return reduce(lambda _, e: e(self), decorators, self)

    def draw(self):
        for drawable in self.drawables:
            drawable.draw()
        return self

    def update(self, *a: P.args, **b: P.kwargs):
        drawable = self.component(*a, **b)
        self.drawables = drawable if isinstance(drawable, Iterable) else (drawable,)

    def show(self, *a: P.args, **b: P.kwargs):
        """
        :lifecycle-hook show: before first flip
        :lifecycle-hook flip: after first flip
        :lifecycle-hook frame: before reflip
        :lifecycle-hook poll: after reflip
        :lifecycle-hook close: call `self.close`
        """
        self.shown = True
        self.data.clear()
        self.data["frame_times"] = []
        self.update(*a, **b)
        self.emit("show")
        # first draw
        if not self.win.waitBlanking:
            logging.warning("Window.waitBlanking should be True")
        self.data["frame_times"].append(self.draw().win.flip())
        self.emit("flip")
        # polling loop
        while self.shown:
            if self.timer():
                self.close()
                break
            self.emit("frame")
            self.data["frame_times"].append(self.draw().win.flip())
            self.emit("poll")
        return self.data.copy()

    def close(self, *_):
        self.shown = False
        self.emit("close")


@dataclass
class Context:
    win: visual.Window = field(default_factory=visual.Window)
    exp: data.ExperimentHandler = field(default_factory=data.ExperimentHandler)

    def scene(self, comp: Component[P] | type[Component[P]]):
        """create scene with component"""
        return Scene(self.win, comp)

    def record(self, **kwargs: float | str | bool):
        """add a row to `self.exp`"""
        for k, v in kwargs.items():
            self.exp.addData(k, v)
        self.exp.nextEntry()
