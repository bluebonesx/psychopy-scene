import random

from psychopy import visual
from psychopy.visual import rect

from psychopy_scene import Context, Scene
from psychopy_scene import decorator as deco

ctx = Context()
ctx.exp.saveWideText = False
ctx.exp.savePickle = False
stim = visual.TextStim(ctx.win)


@deco.close_on("mouse_right")
@deco.event_mouse()
@ctx.scene
class multi_box:
    scene: Scene
    boxes = {
        rect.Rect(
            ctx.win, pos=(random.random() * 2 - 1, random.random() * 2 - 1), size=0.1
        )
        for _ in range(4)
    }
    stims = list(boxes) + [stim]

    def __call__(self):
        stim.text = "Click box to hide it\nhide all boxes to exit"
        return self.stims

    def on_mouse_left(self, _):
        for stim in self.stims:
            if stim in self.boxes and deco.event_mouse.mouse.isPressedIn(stim):
                self.stims.remove(stim)
        if len(self.stims) == 1:
            self.scene.close()


multi_box.show()
