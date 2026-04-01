from psychopy import visual, data
from psychopy_scene import Context, Scene, decorator as deco

ctx = Context(exp=data.ExperimentHandler(dataFileName='data.csv', autoLog=False))
scene = lambda comp: ctx.scene(comp).use(
    deco.close_on('key_escape'),
    deco.hardware_keyboard(),
)

top_stim = visual.TextStim(ctx.win, pos=(0,0.5))
bot_stim = visual.TextStim(ctx.win, pos=(0,-0.5))

@scene
class test_key:
    scene: Scene
    def __call__(self):
        top_stim.text = 'press any key to display\npress escape key to exit'
        bot_stim.text = ''
        return top_stim, bot_stim
    def on_key_any(self, e):
        bot_stim.text = e

@deco.event_mouse()
@scene
class test_mouse:
    scene: Scene
    def __call__(self):
        top_stim.text = 'press any mouse to display\npress escape key to exit'
        bot_stim.text = ''
        return top_stim, bot_stim
    def on_mouse_any(self, e):
        bot_stim.text = e

@ctx.scene
class test_duration:
    scene: Scene
    def __call__(self):
        top_stim.text = self.__class__.__name__
        bot_stim.text = ''
        return top_stim, bot_stim
    def on_frame(self, _):
        frame_times = self.scene.data['frame_times']
        bot_stim.text = f"frames: {len(frame_times)}\nduration: {frame_times[-1] - frame_times[0]:.2f}"
    

test_duration.use(deco.duration(2)).show();
test_key.show();
test_mouse.show();
test_duration.use(deco.duration(3)).show();
