# PsychoPy-Scene

![PyPI - Version](https://img.shields.io/pypi/v/psychopy-scene)
![PyPI - Downloads](https://img.shields.io/pypi/dm/psychopy-scene)

[English](README.md) | 简体中文

基于 Scene 架构的轻量级框架，for [PsychoPy](https://github.com/psychopy/psychopy)

> [!NOTE]
> 本项目处于早期开发阶段，使用时请固定版本号。

## 特性

- 轻量级：只有 2 个文件，无额外依赖项
- 类型安全：泛型支持
- 新人友好：仅需掌握 `Context` 和 `Scene` 的概念即可上手

## 安装

```bash
pip install psychopy-scene
```

## 快速上手

### 上下文

`Context` 用于封装画面 scene 间共享的数据，比如绘制窗口 `Window`。
编写实验的第一步，就是创建实验上下文。

```python
from psychopy import visual, data
from psychopy_scene import Context

ctx = Context(win=visual.Window(), exp=data.ExperimentHandler())
```

### 画面

实验可以被当作一系列画面 scene 的组合，编写实验程序只需要 2 步：

1. 创建画面
2. 编写画面呈现逻辑

通过装饰器创建画面：

```python
from psychopy import visual
from psychopy.hardware import keyboard
from psychopy_scene.decorator import duration, hardware_keyboard

# create stimulus
stim_1 = visual.TextStim(ctx.win, text="Hello")
stim_2 = visual.TextStim(ctx.win, text="World")

# create scene
@duration(1)
@ctx.scene
def demo_1(color: str, ori: float):
    print('it will be called before first flip')
    stim_1.color = color
    stim_2.ori = ori
    return stim_1, stim_2

@close_on('key_space')
@hardware_keyboard()
@ctx.scene
class demo_2:
    scene: Scene
    def __call__(self, text: str):
        stim_1.text = text
        return stim_1
    def on_key_space(self, evt: keyboard.KeyPress):
        self.scene.data['rt'] = evt.tDown - self.scene.data['frame_times'][0]

# show scene
data_1 = demo_1.show(color="red", ori=45)
data_2 = demo_2.show(text="test")
```

> [!IMPORTANT]
> 装饰器会改变 scene 的状态，它们通过 scene 实例暴露的 api 实现这点

时间相关的装饰器会相互覆盖，因为它们通过设置 scene.timer 属性起作用。

这在一些场景中很有用，比如呈现时间不固定的画面：

```python
@duration(1)
@ctx.scene
def demo():
    return stim

data = demo.use(duration(0.5)).show()
```

### 数据

scene 会自动收集数据：

| 名称        | 描述             |
| ----------- | ---------------- |
| frame_times | 每帧 flip 时间戳 |

可以通过 `scene.data` 访问这些数据：

```python
@close_on('key_f', 'key_j')
@hardware_keyboard()
@ctx.scene
def demo():
    return stim

data = demo.show() # just a dict
show_time = data["frame_times"][0]
```

也支持手动收集数据：

```python
@hardware_keyboard()
@ctx.scene
class demo:
    scene: Scene
    def __call__(self):
        return stim
    def on_key_f(self, evt: keyboard.KeyPress):
        self.scene.data['pressed_duration'] = evt.duration

data = demo.show()
duration = data['pressed_duration']
```

### 事件

事件表示 scene 呈现时的某个特定时机，比如按下某个键、鼠标点击等。
要想在事件发生时执行一些操作，我们需要为事件添加回调函数:

```py
scene.on('show', lambda _: print('do something'));
```

这是 scene 全部内置事件及其触发时机：

```mermaid
graph TD
初始化 --> s((show)) --> 首次绘制 --> f((flipped)) --> c{是否绘制？}
c -->|否| 停止
c -->|是| 计时检测 --> a((frame)) --> 重绘 --> p((poll)) --> c
```

有些事件类型由输入设备相关的装饰器提供，比如 `hardware_keyboard` 提供了对 `key_space` 事件的支持，让那些通过 `scene.on('key_space', ...)` 添加的回调函数能在按下 `sapce` 键被触发。

这些装饰器会在 `poll` 事件触发时通过 `scene.emit('key_space', ...)` 触发其他事件，实现对某些事件的支持。

## 示例

### Trial

```python
from psychopy import visual
from psychopy_scene import Context
from psychopy_scene.decorator import duration

def task(ctx: Context, sec = 1):
    stim = visual.TextStim(ctx.win, text="")
    scene = ctx.scene(lambda: stim).use(duration(sec))
    data = scene.show()
    ctx.record(time=data['frame_times'][0])
```

### Block

```python
from psychopy import visual
from psychopy_scene import Context
from psychopy_scene.decorator import duration

def task(ctx: Context):
    stim = visual.TextStim(ctx.win, text="")
    scene = ctx.scene(lambda: stim).use(duration(1))
    data = scene.show()
    ctx.record(time=data['frame_times'][0])

win = visual.Window()
data = []
for block_index in range(10):
    ctx = Context(win)
    ctx.exp.extraInfo['block_index'] = block_index
    task(ctx)
    block_data = ctx.exp.getAllEntries()
    data.extends(block_data)
```
