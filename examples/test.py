from psychopy import visual
from psychopy.hardware import keyboard

from psychopy_scene import Context, Scene
from psychopy_scene import decorator as deco

ctx = Context()
ctx.exp.saveWideText = False
ctx.exp.savePickle = False
top_stim = visual.TextStim(ctx.win, pos=(0, 0.5))
bot_stim = visual.TextStim(ctx.win, pos=(0, -0.5))

deco.hardware_keyboard.kb = keyboard.Keyboard(backend="iohub")


@deco.close_on("key_escape")
@deco.hardware_keyboard()
@ctx.scene
class test_key:
    scene: Scene

    def __call__(self):
        top_stim.text = "press any key to display\npress escape key to continue"
        bot_stim.text = ""
        return top_stim, bot_stim

    def on_key_any(self, e):
        bot_stim.text = e


@deco.event_mouse()
@deco.close_on("key_escape")
@deco.hardware_keyboard()
@ctx.scene
class test_mouse:
    scene: Scene

    def __call__(self):
        top_stim.text = "press any mouse to display\npress escape key to continue"
        bot_stim.text = ""
        return top_stim, bot_stim

    def on_mouse_any(self, e):
        bot_stim.text = e


@deco.record_frames
@deco.close_on("key_escape")
@deco.hardware_keyboard()
@ctx.scene
class test_duration:
    scene: Scene

    def __call__(self, sec: float):
        self.scene.data.update(sec=sec)
        top_stim.text = f"stop after {sec} sec\npress escape key to continue"
        bot_stim.text = ""
        return top_stim, bot_stim

    def on_redraw(self, t: float):
        frame_times = self.scene.data["frame_times"]
        if (
            t - self.scene.data["start_time"]
            < self.scene.data["sec"] - self.scene.win.monitorFramePeriod / 2
        ):
            bot_stim.text = f"n_frames: {len(frame_times)}\nduration: {t - self.scene.data['start_time']:.2f}"


test_duration.show(0.1)
test_duration.show(0.5)
test_duration.show(1)
test_key.show()
test_mouse.show()
