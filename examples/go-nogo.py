from psychopy import visual
from psychopy.hardware import keyboard

from psychopy_scene import Context, Scene
from psychopy_scene import decorator as deco

ctx = Context()
ctx.exp.saveWideText = False
ctx.exp.savePickle = False
stim = visual.TextStim(ctx.win)


# fixation
@deco.duration(0.5)
@ctx.scene
def fixation():
    stim.text = "+"
    return stim


# go-nogo
@deco.duration(1)
@deco.close_on("key_space")
@deco.hardware_keyboard()
@ctx.scene
class gng:
    scene: Scene

    def __call__(self, isgo: bool):
        stim.text = "X" if isgo else "O"
        return stim

    def on_key_space(self, evt: keyboard.KeyPress):
        show_time = self.scene.data["frame_times"][0]
        self.scene.data["rt"] = evt.tDown - show_time


# feedback
@deco.duration(1)
@ctx.scene
def feedback(correct: bool):
    stim.text = "Y" if correct else "N"
    return stim


# trial
for isgo in (True, False):
    fixation.show()
    data = gng.show(isgo)
    feedback.show(isgo == ("rt" in data))
