# Artisan烘焙软件新功能实现计划

## 功能需求
在开始记录烘焙曲线前，新增一个功能：
1. 提供输入框，设定预计的入豆温度和达到该温度的RoR（升温速率）
2. 显示趋势线，实时查看当前RoR是否满足要求
3. 若预计在5秒后能满足特定RoR到达指定温度，在画面上提醒

## 项目分析总结

### 现有架构
1. **主窗口**: `src/artisanlib/main.py` - `ApplicationWindow` 类，程序化UI构建
2. **RoR计算**:
   - `src/artisanlib/canvas.py` - `polyRoR()` 和 `arrayRoR()` 方法
   - `src/artisanlib/main.py` - `RoR()` 函数计算各阶段RoR
3. **温度数据存储**:
   - 豆温: `self.qmc.temp2`
   - 环温: `self.qmc.temp1`
   - 时间戳: `self.qmc.timex`
   - 入豆事件索引: `self.qmc.timeindex[0]`
4. **报警系统**: `src/artisanlib/alarms.py` - 完整的报警设置和触发机制
5. **通知系统**: `src/artisanlib/notifications.py` - `NotificationManager` 类

### 现有RoR计算机制
1. **计算方法**: 多项式拟合和直接差分法
2. **数据关联**: 温度数组与时间数组同步
3. **入豆温度**: 通过 `timeindex[0]` 索引记录
4. **预测功能**: 已有 `AUCguideFlag` 和线性温度预测模式

### 配置保存机制
基于用户选择"保存到用户配置"，需要扩展现有配置系统：
1. **现有配置系统**: 使用 `QSettings` 保存用户偏好
2. **新配置键**:
   - `TargetChargeTemp`: 目标入豆温度
   - `TargetChargeRoR`: 目标RoR
   - `ChargeTargetEnabled`: 功能启用状态
3. **配置文件位置**:
   - Windows: `%APPDATA%\Roaming\Artisan\artisan.ini`
   - macOS: `~/Library/Preferences/artisan.ini`
   - Linux: `~/.config/artisan/artisan.ini`
4. **配置管理**:
   - 对话框关闭时保存当前设置
   - 应用程序启动时加载默认设置
   - 支持重置为默认值

## 实现方案设计

### 1. 数据模型扩展
在 `qmc`（质量管理控制）类中新增字段：
```python
class QMC:
    # 现有字段...
    target_charge_temp: float = 0.0        # 目标入豆温度
    target_charge_ror: float = 0.0         # 目标入豆RoR
    charge_temp_met: bool = False          # 是否达到目标温度
    ror_prediction_seconds: int = 5        # 预测时间窗口（默认5秒）
```

### 2. UI组件添加 - 专用对话框方案
基于用户选择，创建一个专用的对话框 `ChargeTempRorDlg`：
- **位置**: 通过主窗口按钮打开专用对话框
- **继承**: `ArtisanDialog`（遵循现有对话框模式）
- **对话框控件**:
  1. `target_charge_temp_spinbox: QDoubleSpinBox` - 目标入豆温度输入 (°C/°F)
  2. `target_ror_spinbox: QDoubleSpinBox` - 目标RoR输入 (°C/°F per min)
  3. `enabled_checkbox: QCheckBox` - 启用/禁用开关
  4. `current_ror_label: QLabel` - 实时RoR显示
  5. `prediction_label: QLabel` - 预测状态显示
  6. `save_button: QPushButton` - 保存按钮
  7. `cancel_button: QPushButton` - 取消按钮
- **主窗口按钮**: 在 `ApplicationWindow` 的工具栏中添加 "Charge Target" 按钮

### 3. RoR预测算法
基于现有RoR计算方法扩展，在 `canvas.py` 中添加新方法：

```python
def predict_charge_time(self, current_temp: float, current_ror: float,
                       target_temp: float, target_ror: float) -> Optional[float]:
    """
    基于当前温度和RoR，预测达到目标温度的时间（秒）
    使用线性插值方法，考虑目标RoR
    返回: 预测时间（秒），如果无法预测返回None
    """
    if current_ror <= 0 or target_ror <= 0:
        return None

    # 计算平均RoR（当前RoR和目标RoR的平均值）
    avg_ror = (current_ror + target_ror) / 2
    # 温度差
    temp_diff = target_temp - current_temp
    if temp_diff <= 0:
        return 0.0  # 已经达到目标

    # 计算所需时间：温度差 / 平均RoR，转换为秒
    time_minutes = temp_diff / avg_ror
    return time_minutes * 60.0

def should_show_charge_annotation(self) -> bool:
    """
    判断是否应该显示入豆目标标注
    条件: 功能启用、活跃且预测在设定时间内能达到目标温度
    """
    if not self.qmc.charge_target_enabled:
        return False

    if not self.qmc.charge_target_active:
        return False

    prediction_time = self.qmc.charge_prediction_time

    return 0 < prediction_time <= self.qmc.ror_prediction_seconds

def calculate_current_ror(self, window_seconds: int = 30) -> float:
    """
    计算当前RoR，基于最近的数据点
    使用现有的polyRoR()方法
    """
    if len(self.qmc.timex) < 2:
        return 0.0

    # 获取最近的温度和时间数据
    recent_indices = self.get_recent_indices(window_seconds)
    if len(recent_indices) < 2:
        return 0.0

    # 使用现有的RoR计算方法
    return self.polyRoR(self.qmc.timex, self.qmc.temp2,
                       window_seconds, recent_indices[-1])
```

### 4. 趋势线显示 - 图表标注方案
基于用户选择的"图表上标注"提醒形式，在 `canvas.py` 中添加图表标注功能：

```python
class ChargeTargetAnnotation:
    """
    入豆目标图表标注类，在图表上显示目标温度和预测信息
    使用现有matplotlib标注系统
    """
    def __init__(self, ax, target_temp: float, prediction_time: float):
        self.ax = ax
        self.target_temp = target_temp
        self.prediction_time = prediction_time
        self.hline = None  # 水平温度线
        self.vline = None  # 垂直时间线
        self.text_annotation = None
        self.marker_point = None

    def draw(self):
        """
        绘制标注元素
        样式: 亮黄色虚线，圆形标记点，文本标注
        """
        # 绘制水平目标温度线
        self.hline = self.ax.axhline(y=self.target_temp,
                                     color='#FFD700',  # 亮黄色
                                     linestyle='--',   # 虚线
                                     linewidth=1.5,
                                     alpha=0.8)

        # 如果预测时间有效，绘制垂直时间线和标记点
        if self.prediction_time > 0:
            current_time = self.ax.get_xlim()[1]  # 当前图表时间
            target_time = current_time + self.prediction_time

            # 垂直时间线
            self.vline = self.ax.axvline(x=target_time,
                                        color='#FFA500',  # 橙色
                                        linestyle=':',
                                        linewidth=1.0,
                                        alpha=0.6)

            # 标记点
            self.marker_point = self.ax.plot(target_time, self.target_temp,
                                            marker='o',
                                            color='#FF4500',  # 橙红色
                                            markersize=8,
                                            markeredgecolor='white',
                                            markeredgewidth=1)[0]

        # 文本标注
        self.text_annotation = self.ax.annotate(
            f'Target: {self.target_temp:.1f}°C\nPrediction: {self.prediction_time:.1f}s',
            xy=(target_time, self.target_temp),
            xytext=(10, 10),
            textcoords='offset points',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
            fontsize=9
        )

    def update(self, target_temp: float, prediction_time: float):
        """
        更新标注信息
        """
        self.target_temp = target_temp
        self.prediction_time = prediction_time

        # 清除旧标注
        if self.hline:
            self.hline.remove()
        if self.vline:
            self.vline.remove()
        if self.marker_point:
            self.marker_point.remove()
        if self.text_annotation:
            self.text_annotation.remove()

        # 绘制新标注
        self.draw()

    def set_visible(self, visible: bool):
        """
        设置标注可见性
        """
        for element in [self.hline, self.vline, self.marker_point, self.text_annotation]:
            if element:
                element.set_visible(visible)
```

**标注触发逻辑**:
1. 在每次图表重绘时检查 `should_show_charge_annotation()`
2. 如果条件满足，创建或更新 `ChargeTargetAnnotation` 对象
3. 当达到目标温度或功能禁用时，移除标注

### 5. 提醒机制 - 图表标注触发
基于用户选择的"图表上标注"方案，集成到现有报警系统：

#### 报警类型扩展（在 `alarms.py` 中添加）：
```python
# 定义新的报警类型
CHARGE_TARGET_REACHED = 'ChargeTargetReached'

# 在报警类型枚举中添加
class AlarmType:
    # 现有类型...
    CHARGE_TARGET_REACHED = CHARGE_TARGET_REACHED

# 在报警配置中添加对应的设置项
class AlarmSettings:
    # 现有设置...
    charge_target_threshold = 5.0  # 默认5秒
```

#### 触发逻辑集成：
```python
def check_charge_target(self) -> bool:
    """
    检查入豆目标条件，如果预测5秒内能达到目标温度
    返回True表示应该触发图表标注
    """
    # 1. 检查功能是否启用
    if not self.qmc.charge_target_enabled:
        return False

    # 2. 获取当前温度
    if len(self.qmc.temp2) == 0:
        return False

    current_temp = self.qmc.temp2[-1]

    # 3. 获取当前RoR
    current_ror = self.calculate_current_ror()

    # 4. 计算预测时间
    prediction_time = self.predict_charge_time(
        current_temp,
        current_ror,
        self.qmc.target_charge_temp,
        self.qmc.target_charge_ror
    )

    # 5. 更新qmc预测时间字段
    self.qmc.charge_prediction_time = prediction_time if prediction_time else 0.0

    # 6. 判断是否应该触发（5秒内）
    self.qmc.charge_prediction_valid = (
        prediction_time is not None and
        0 < prediction_time <= 5.0
    )

    # 7. 同时触发通知系统（可选，作为备份）
    if self.qmc.charge_prediction_valid:
        self.aw.sendmessage(f'Charge target will be reached in {prediction_time:.1f}s')

    return self.qmc.charge_prediction_valid
```

#### 标注触发时机：
1. **实时更新**: 在每次图表重绘时调用 `check_charge_target()`
2. **标注管理**: 通过 `ChargeTargetAnnotation.update()` 方法更新图表标注
3. **状态同步**: 标注可见性与 `charge_target_enabled` 和 `charge_prediction_valid` 状态同步

## 详细实施步骤

### 阶段1：数据模型扩展（预计时间：2小时）
#### 1.1 修改 `src/artisanlib/atypes.py`（或相关数据类）：
```python
# 在 QMC 类中添加新字段
class QMC:
    # 现有字段...
    target_charge_temp: float = 180.0        # 目标入豆温度 (默认180°C)
    target_charge_ror: float = 25.0          # 目标入豆RoR (默认25°C/min)
    charge_target_enabled: bool = False      # 功能启用状态
    charge_prediction_time: float = 0.0     # 预测达到时间（秒）
    charge_prediction_valid: bool = False   # 预测有效性标志
    ror_prediction_seconds: int = 5         # 预测时间窗口（默认5秒）
    charge_target_active: bool = True       # 功能活跃状态（入豆前活跃，charge后停止）
```

#### 1.2 更新 `canvas.py` 中的 `__slots__` 列表：
```python
# 在 tgraphcanvas 类的 __slots__ 列表中添加：
'target_charge_temp',
'target_charge_ror',
'charge_target_enabled',
'charge_prediction_time',
'charge_prediction_valid',
'charge_target_active',
```

#### 1.3 更新 `canvas.py` 构造函数：
```python
def __init__(self, ...):
    # 现有初始化...
    self.target_charge_temp: float = 180.0
    self.target_charge_ror: float = 25.0
    self.charge_target_enabled: bool = False
    self.charge_prediction_time: float = 0.0
    self.charge_prediction_valid: bool = False
    self.charge_target_active: bool = True  # 入豆前活跃，charge后停止
```

### 阶段2：配置系统扩展（预计时间：1小时）
#### 2.1 在 `ApplicationWindow` 中添加配置加载方法（main.py）：
```python
def load_charge_target_settings(self):
    """
    加载入豆目标配置
    """
    settings = QSettings()
    self.qmc.target_charge_temp = settings.value(
        'TargetChargeTemp', 180.0, type=float)
    self.qmc.target_charge_ror = settings.value(
        'TargetChargeRoR', 25.0, type=float)
    self.qmc.charge_target_enabled = settings.value(
        'ChargeTargetEnabled', False, type=bool)
```

#### 2.2 在 `ApplicationWindow` 的初始化中调用：
```python
def __init__(self, ...):
    # 现有初始化...
    self.load_charge_target_settings()
```

### 阶段3：对话框实现（预计时间：3小时）
#### 3.1 创建新对话框类 `ChargeTempRorDlg`：
**方案A**：添加到 `src/artisanlib/dialogs.py`（推荐，保持代码集中）
**方案B**：新建文件 `src/artisanlib/charge_dialog.py`

#### 3.2 对话框UI设计：
```python
class ChargeTempRorDlg(ArtisanDialog):
    def __init__(self, parent=None, aw=None):
        super().__init__(parent, aw)
        self.setup_ui()
        self.load_current_settings()
        self.connect_signals()

    def setup_ui(self):
        """创建对话框控件"""
        # 布局设置...
        self.target_temp_spinbox = MyQDoubleSpinBox()
        self.target_ror_spinbox = MyQDoubleSpinBox()
        self.enabled_checkbox = QCheckBox(self.tr('Enabled'))
        self.save_button = QPushButton(self.tr('Save'))
        self.cancel_button = QPushButton(self.tr('Cancel'))

    def load_current_settings(self):
        """加载当前设置"""
        self.target_temp_spinbox.setValue(self.aw.qmc.target_charge_temp)
        self.target_ror_spinbox.setValue(self.aw.qmc.target_charge_ror)
        self.enabled_checkbox.setChecked(self.aw.qmc.charge_target_enabled)

    def connect_signals(self):
        """连接信号"""
        self.save_button.clicked.connect(self.save_and_close)
        self.cancel_button.clicked.connect(self.close)

    def save_and_close(self):
        """保存设置并关闭对话框"""
        # 保存到qmc对象
        self.aw.qmc.target_charge_temp = self.target_temp_spinbox.value()
        self.aw.qmc.target_charge_ror = self.target_ror_spinbox.value()
        self.aw.qmc.charge_target_enabled = self.enabled_checkbox.isChecked()

        # 保存到配置文件
        settings = QSettings()
        settings.setValue('TargetChargeTemp', self.aw.qmc.target_charge_temp)
        settings.setValue('TargetChargeRoR', self.aw.qmc.target_charge_ror)
        settings.setValue('ChargeTargetEnabled', self.aw.qmc.charge_target_enabled)

        self.close()
```

### 阶段4：主窗口集成（预计时间：2小时）
#### 4.1 在 `ApplicationWindow` 中添加对话框实例：
```python
def __init__(self, ...):
    # 现有初始化...
    self.charge_dialog = None  # 延迟创建

def show_charge_target_dialog(self):
    """显示入豆目标设置对话框"""
    if self.charge_dialog is None:
        self.charge_dialog = ChargeTempRorDlg(self, self)
    self.charge_dialog.show()
    self.charge_dialog.raise_()
    self.charge_dialog.activateWindow()
```

#### 4.2 在工具栏中添加按钮：
```python
def create_charge_target_button(self):
    """创建入豆目标按钮"""
    charge_action = QAction(self.tr('Charge Target'), self)
    charge_action.setStatusTip(self.tr('Set charge temperature and RoR target'))
    charge_action.triggered.connect(self.show_charge_target_dialog)

    # 添加到工具栏
    self.toolbar.addAction(charge_action)
```

### 阶段5：RoR预测算法实现（预计时间：2小时）
#### 5.1 在 `canvas.py` 中添加预测方法（已在前文描述）：
- `predict_charge_time()` - 预测达到目标温度的时间
- `calculate_current_ror()` - 计算当前RoR
- `should_show_charge_annotation()` - 判断是否应该显示标注

#### 5.2 集成到现有RoR计算系统：
```python
def update_charge_prediction(self):
    """
    更新入豆目标预测信息
    在图表重绘时调用。入豆（charge）事件发生后停止功能。
    """
    # 1. 检查功能是否启用
    if not self.qmc.charge_target_enabled:
        return

    # 2. 检查是否已经过了charge阶段
    # timeindex[0] 记录charge事件的时间索引
    if hasattr(self.qmc, 'timeindex') and len(self.qmc.timeindex) > 0:
        charge_index = self.qmc.timeindex[0]
        if charge_index >= 0:  # 有效的charge事件已发生
            self.qmc.charge_target_active = False
            # 如果已有标注，将其隐藏
            if self.charge_annotation:
                self.charge_annotation.set_visible(False)
            return

    # 3. 检查功能活跃状态
    if not self.qmc.charge_target_active:
        return

    # 4. 计算当前RoR和预测时间
    current_ror = self.calculate_current_ror()
    current_temp = self.qmc.temp2[-1] if len(self.qmc.temp2) > 0 else 0

    prediction_time = self.predict_charge_time(
        current_temp,
        current_ror,
        self.qmc.target_charge_temp,
        self.qmc.target_charge_ror
    )

    # 5. 更新qmc状态
    self.qmc.charge_prediction_time = prediction_time or 0.0
    self.qmc.charge_prediction_valid = (
        prediction_time is not None and
        0 < prediction_time <= self.qmc.ror_prediction_seconds
    )

    # 6. 通知系统（可选）
    if self.qmc.charge_prediction_valid:
        self.aw.sendmessage(
            f'Charge target will be reached in {prediction_time:.1f}s'
        )
```

### 阶段6：图表标注实现（预计时间：3小时）
#### 6.1 创建 `ChargeTargetAnnotation` 类（已在前文描述）：
- 水平目标温度线
- 垂直预测时间线
- 标记点和文本标注
- 可见性控制方法

#### 6.2 集成到图表重绘系统：
```python
def redraw(self):
    """重绘图表，包括入豆目标标注"""
    # 现有重绘逻辑...

    # 更新预测
    self.update_charge_prediction()

    # 管理标注
    if self.should_show_charge_annotation():
        if self.charge_annotation is None:
            self.charge_annotation = ChargeTargetAnnotation(
                self.ax,
                self.qmc.target_charge_temp,
                self.qmc.charge_prediction_time
            )
            self.charge_annotation.draw()
        else:
            self.charge_annotation.update(
                self.qmc.target_charge_temp,
                self.qmc.charge_prediction_time
            )
            self.charge_annotation.set_visible(True)
    elif self.charge_annotation is not None:
        self.charge_annotation.set_visible(False)
```

### 阶段7：报警系统集成（预计时间：2小时）
#### 7.1 在 `alarms.py` 中添加新报警类型：
```python
# 定义新报警类型常量
CHARGE_TARGET_REACHED = 'ChargeTargetReached'

# 在报警配置中添加对应的设置项
class AlarmSettings:
    # 现有设置...
    charge_target_threshold = 5.0  # 默认5秒

# 在报警检查中添加新类型
def check_charge_target(self):
    """检查入豆目标条件"""
    return (
        self.qmc.charge_target_enabled and
        self.qmc.charge_target_active and
        self.qmc.charge_prediction_valid
    )
```

#### 7.2 集成到现有报警循环：
```python
def check_alarms(self):
    """检查所有报警条件"""
    # 现有报警检查...

    # 新条件：入豆目标
    if self.check_charge_target():
        self.trigger_alarm(CHARGE_TARGET_REACHED)
```

### 阶段8：测试和验证（预计时间：2小时）
#### 8.1 单元测试：
- 预测算法正确性测试
- 配置保存/加载测试
- 对话框交互测试

#### 8.2 集成测试：
- 与现有报警系统集成测试
- 图表标注显示测试
- 实时数据流测试

#### 8.3 UI测试：
- 对话框布局验证
- 国际化文本显示
- 按钮和控件交互

## 关键文件修改清单

### 主要修改文件：
1. `src/artisanlib/main.py` - UI组件添加和事件处理
2. `src/artisanlib/canvas.py` - 预测算法和趋势线绘制
3. `src/artisanlib/alarms.py` - 报警条件扩展
4. `src/artisanlib/atypes.py` - 数据模型扩展
5. `src/artisanlib/notifications.py` - 提醒集成

### 配置文件：
1. 用户偏好设置文件
2. 报警配置文件
3. 国际化文件（翻译）

## 国际化考虑
1. 新增字符串添加到翻译文件
2. 支持多语言单位显示（℃/℉）

## 风险与挑战
1. **RoR预测精度**: 基于线性预测可能不够准确
2. **实时性能**: 频繁计算RoR预测可能影响界面响应
3. **UI布局**: 在已有复杂界面中添加新组件需要谨慎设计
4. **向后兼容**: 现有用户配置需要兼容

## 测试策略
1. **单元测试**: 预测算法和RoR计算
2. **集成测试**: 与现有报警系统集成
3. **UI测试**: 输入验证和交互
4. **性能测试**: 实时计算性能影响