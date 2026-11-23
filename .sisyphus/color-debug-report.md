# ArtisanZ 曲线颜色问题调试报告

## 问题现象

用户打开 ArtisanZ 曲线图，看到：
1. **BT/ET 背景曲线（参考烘焙曲线）显示为黑色**，与 Colors 对话框设定的颜色不一致
2. **阶段色带（Drying/Maillard/Development）颜色太深、线框太粗**
3. 主曲线颜色也可能偏灰

## 已确认的事实

### 1. Palette 值是正确的

在 `drawBT()` 函数内部加了调试打印，用户确认输出为：
```
[DEBUG-DRAWBT] palette['bt']=#3A7CA5 palette1['bt']=#3A7CA5
```
`#3A7CA5` 是海洋蓝，不是黑色。说明 palette 字典里的值是正确的新色值。

### 2. matplotlib 能正确渲染该颜色

用 matplotlib 独立测试 `#3A7CA5`：
```python
ax.plot([0,1], [1,1], color='#3A7CA5', linewidth=2)
```
结果：清晰的蓝色线条。颜色值本身没有问题。

### 3. 代码确实在运行

用户通过终端运行 `./.venv/bin/python artisan.py`，能看到调试输出。代码修改确实生效。

## 尝试过的修复（全部失败）

### 尝试 1：修改 DEFAULT_GRAPH_PALETTE 默认色值
- 文件：`src/artisanlib/canvas.py` 第 189-194 行
- 操作：将 `'et': '#A76557'` 改为 `'et': '#C0504D'`，`'bt': '#4E7180'` 改为 `'bt': '#3A7CA5'` 等
- 结果：**无效**

### 尝试 2：重命名主题文件 Default.athm
- 文件：`includes/Themes/Artisan/Default.athm` → `.bak`
- 原因：`changeGColor(1)` ("Restore Defaults" 按钮) 会加载该主题文件，其中含旧色值
- 结果：**无效**

### 尝试 3：在 loadSettings() 中添加条件迁移
- 文件：`src/artisanlib/main.py` ~第 18924 行
- 操作：QSettings 加载 Colors 后，检查旧值并替换
- 问题：条件匹配太脆弱（QSettings 可能存 8 位 RGBA、不同大小写）
- 结果：**无效**

### 尝试 4：在 loadSettings() 中强制覆盖（PaletteMigrated_v2 标记）
- 操作：不看旧值格式，直接写入新色值
- 问题：`loadSettings()` 迁移设置了标记，但后续 `fetchCurveStyles()` 也有 `getColor()` 调用
- 结果：**无效**

### 尝试 5：在 fetchCurveStyles() 末尾添加覆盖
- 文件：`src/artisanlib/main.py` ~第 20660 行
- 操作：在所有 `getColor()` 调用之后，强制写入新 palette + `l_temp1.set_color()` 等
- 问题：`fetchCurveStyles()` **不在启动序列中调用**——只在 `edit_parameters()` 中调用
- 结果：**无效**

### 尝试 6：使用 PaletteMigrated_v3 新标记
- 原因：v2 标记被 loadSettings 提前设置，导致 fetchCurveStyles 跳过
- 结果：**无效**（因为 fetchCurveStyles 本来就不在启动时调用）

### 尝试 7：删除 QSettings 中的旧色值（PaletteMigrated_v4）
- 操作：`settings.remove('Colors')`, `settings.remove('ETBColor')`, `settings.remove('BTBColor')`
- 原因：删除后 palette 会回退到 DEFAULT_GRAPH_PALETTE 默认值
- 结果：**无效**

### 尝试 8：禁用 path_effects
- 文件：`src/artisanlib/canvas.py` drawET/drawBT
- 操作：将 `path_effects=self.line_path_effects(...)` 改为 `path_effects=[]`
- 原因：path_effects 用 `palette['background']` 画描边，如果 background 是深色会覆盖曲线
- 验证：`palette['background'] = '#FFFDF8'`（近白色），不是黑色
- 结果：**无效**

### 尝试 9：在 drawBT() 内部添加颜色守卫
- 操作：在 `self.ax.plot()` 之前检查 palette['bt']，如果是旧值则替换
- 问题：palette['bt'] 已经是新值 `#3A7CA5`，守卫不触发
- 结果：**无效**（palette 本身就是对的）

### 尝试 10：硬编码背景曲线颜色
- 文件：`src/artisanlib/canvas.py` 第 10640/10667 行
- 操作：将 `color=self.backgroundmetcolor` 改为 `color='#E08070'`
- 结果：**无效**（用户报告仍无变化）

## 关键代码路径

### 颜色加载链（启动时）
```
canvas.__init__():
  self.palette = DEFAULT_GRAPH_PALETTE.copy()     ← 新色值（已改）
  self.palette1 = self.palette.copy()
  self.backgroundmetcolor = self.palette['et']     ← '#C0504D'
  self.backgroundbtcolor = self.palette['bt']      ← '#3A7CA5'

main.loadSettings():
  QSettings 'Colors' dict → self.qmc.palette[k]    ← 可能覆盖为新或旧值
  QSettings 'ETBColor' → self.qmc.backgroundmetcolor ← 可能覆盖
  QSettings 'BTBColor' → self.qmc.backgroundbtcolor  ← 可能覆盖

main.fetchCurveStyles():  ← 不在启动时调用！只在 edit_parameters() 中
  self.qmc.palette['et'] = self.getColor(self.qmc.l_temp1)
  self.qmc.backgroundmetcolor = self.getColor(self.qmc.l_back1)

canvas.redraw() → drawET()/drawBT():
  color=self.palette['et']  ← 绘图时读取 palette

canvas.redraw() → 背景曲线绘制 (line 10640):
  color=self.backgroundmetcolor, alpha=self.backgroundalpha
```

### DEFAULT_GRAPH_PALETTE 当前值（已修改）
```python
DEFAULT_GRAPH_PALETTE = {
    'background': '#FFFDF8',
    'et': '#C0504D',      # 已从 #A76557 改为珊瑚红
    'bt': '#3A7CA5',      # 已从 #4E7180 改为海洋蓝
    'deltaet': '#D4943A',  # 已从 #C18A6B 改为金色
    'deltabt': '#5B9BD5',  # 已从 #90A1A8 改为天蓝
    'rect1': '#D5DFD0',    # 阶段色带
    'rect2': '#E0D0B8',
    'rect3': '#DCCBD0',
    ...
}
```

### 背景曲线绘制代码
```python
# canvas.py ~line 10640 (背景ET)
self.l_back1, = self.ax.plot(self.timeB, temp_etb,
    color=self.backgroundmetcolor,   # 当前硬编码为 '#E08070'
    alpha=self.backgroundalpha,       # 默认 0.2
    ...)

# canvas.py ~line 10667 (背景BT)
self.l_back2, = self.ax.plot(self.timeB, temp_btb,
    color=self.backgroundbtcolor,    # 当前硬编码为 '#6BAEDB'
    alpha=self.backgroundalpha,
    ...)
```

### QSettings 加载（main.py ~line 18924）
```python
if settings.contains('Colors'):
    for (k, v) in list(settings.value('Colors').items()):
        self.qmc.palette[str(k)] = s2a(toString(v))

self.qmc.backgroundmetcolor = s2a(toString(settings.value('ETBColor', self.qmc.backgroundmetcolor)))
self.qmc.backgroundbtcolor = s2a(toString(settings.value('BTBColor', self.qmc.backgroundbtcolor)))
```

### s2a 函数（util.py）
```python
def s2a(s: str) -> str:
    return str2cmd(s).decode('ascii')
```
已验证：对 hex 色值字符串是 no-op（不改变值）。

## 未解之谜

1. **palette['bt'] = '#3A7CA5'（正确），但渲染为黑色** — matplotlib 能正确渲染此颜色（已独立验证）
2. **硬编码 `color='#E08070'` 在 `self.ax.plot()` 调用中仍然无效** — 这是最不可理解的
3. **禁用 path_effects 也无效** — 排除了描边覆盖的可能
4. **所有修改对用户完全不可见** — 9+ 次代码修改，用户每次重启都说"没有变化"

## 可能的排查方向（供参考）

1. **用户是否真的在运行修改后的代码？** 是否有 .app bundle、Python path 缓存、或其他安装路径覆盖？
2. **QSettings 是否在 macOS 上以非标准方式持久化？** `settings.remove()` 是否真的删除了键？
3. **是否有另一个渲染路径？** 比如 pyqtgraph 渲染器在 matplotlib 之上覆盖？
4. **alpha 值是否导致视觉问题？** `backgroundalpha = 0.2` 可能让浅色线条看起来像黑色
5. **z-order 是否有问题？** 是否有其他元素画在曲线之上？
6. **用户看到的"黑色"是否真的是 #000000？** 还是只是"比预期暗"？截图分析工具可能有误差

## 当前代码状态

- 分支：`ArtisanZ`
- drawET/drawBT 中 path_effects 已禁用（临时）
- 背景曲线颜色已硬编码（临时）
- loadSettings 中有 QSettings 删除迁移（PaletteMigrated_v4）
- fetchCurveStyles 中有未使用的覆盖代码
- 调试日志已清理
