# 入豆目标 (Charge Target) 功能实现总结

**日期**: 2025-12-20  
**状态**: 已完成 (Core Logic, UI, Visualization, Persistence)  
**架构模式**: 领域服务层 (Domain Service Layer) + 测试驱动开发 (TDD)

## 1. 功能概述

该功能允许烘焙师在开始烘焙前设定**目标入豆温度**和**目标升温速率 (RoR)**。系统会根据当前的豆温和 RoR，实时预测达到目标温度所需的时间。如果预测在 5 秒内到达，图表上会出现醒目的黄色标注提示。

## 2. 实施架构

为了避免让原本复杂的 `main.py` 和 `canvas.py` 变得更加臃肿，我们采用了**服务层模式**：
*   **ChargeTargetManager**: 独立的纯逻辑类，负责状态管理和预测计算。
*   **UI层**: 仅负责显示和设置数据，不包含业务逻辑。
*   **集成层**: `main.py` 负责组装各部分。
*   **渲染层**: `canvas.py` 负责向 Manager 询问是否需要绘图，并执行绘图操作。

## 3. 文件变更清单

### 新增文件

1.  **`src/artisanlib/charge_manager.py`**
    *   **作用**: 核心业务逻辑。
    *   **关键方法**: `predict()` (线性预测算法), `should_show_annotation()` (判断显示逻辑), `on_charge_event()` (状态流转)。
    
2.  **`src/artisanlib/charge_dialog.py`**
    *   **作用**: 设置对话框 UI。
    *   **组件**: 目标温度输入、目标 RoR 输入、启用开关。

3.  **`src/test/unitary/artisanlib/test_charge_manager.py`**
    *   **作用**: 单元测试。
    *   **覆盖**: 初始状态、设置更新、预测算法准确性、边界条件（RoR <= 0）、事件处理。

### 修改文件

1.  **`src/artisanlib/main.py`** (ApplicationWindow)
    *   **初始化**: 实例化 `ChargeTargetManager` 并注入到 `qmc` (canvas) 中。
    *   **配置管理**: 在 `settingsLoad` 和 `saveAllSettings` 中添加了对 `TargetChargeTemp`, `TargetChargeRoR`, `ChargeTargetEnabled` 的支持。
    *   **菜单集成**: 在 `Roast` 菜单中添加了 `Charge Target...` 选项。
    *   **交互逻辑**: 添加 `showChargeTargetDialog` 方法，并在设置保存后触发 `redraw()`。

2.  **`src/artisanlib/canvas.py`** (tgraphcanvas)
    *   **架构调整**: 在 `__slots__` 中注册新属性以优化内存。
    *   **绘图逻辑**: 新增 `draw_charge_target_annotation()` 方法。
    *   **钩子埋点**: 在 `redraw` 方法的末尾调用上述绘图方法，实现实时更新。

## 4. 关键代码片段

### 预测逻辑 (ChargeTargetManager)
```python
def predict(self, current_temp: float, current_ror: float) -> Optional[float]:
    # 使用当前 RoR 和目标 RoR 的平均值进行线性预测
    avg_ror_min = (current_ror + self.target_ror) / 2.0
    avg_ror_sec = avg_ror_min / 60.0
    temp_diff = self.target_temp - current_temp
    time_sec = temp_diff / avg_ror_sec
    return time_sec
```

### 渲染钩子 (canvas.py)
```python
# 在 redraw() 方法末尾
self.draw_charge_target_annotation()

def draw_charge_target_annotation(self) -> None:
    # ...获取数据...
    pred_time = self.charge_manager.predict(current_temp, current_ror)
    if self.charge_manager.should_show_annotation():
        # 使用 matplotlib 绘制标注
        self.charge_target_annotation = self.ax.annotate(
            f"Target: {target_temp:.1f}\nIn: {pred_time:.1f}s",
            xy=(target_time, target_temp),
            # ...样式设置...
        )
```

## 5. 待优化与改进建议 (TODO)

虽然功能已上线，但以下方面值得在后续迭代中优化：

### A. 报警系统集成 (高优先级)
*   **现状**: 目前只有视觉提示（黄色标注）。
*   **改进**: 集成到 `src/artisanlib/alarms.py`。当 `should_show_annotation()` 返回 True 时，触发标准的 Artisan 报警（声音、弹窗或背景颜色闪烁）。这对于不时刻盯着屏幕的烘焙师非常重要。

### B. 预测算法升级 (中优先级)
*   **现状**: 简单的线性插值 (基于平均 RoR)。
*   **改进**: 引入二阶多项式拟合或考虑 RoR 的变化率 (加速度)，以更准确地预测非线性升温过程中的到达时间。

### C. 交互体验优化 (低优先级)
*   **现状**: 需要通过菜单打开对话框设置。
*   **改进**: 
    1. 在主工具栏添加快捷按钮。
    2. 支持"一键设定当前温度为目标"。
    3. 在图表上直接拖动目标线来调整温度（交互式绘图）。

### D. 代码结构优化
*   **现状**: `canvas.py` 的 `redraw` 方法过于庞大。
*   **改进**: `draw_charge_target_annotation` 虽然独立了，但仍然在 `tgraphcanvas` 类中。未来可以考虑引入 `Visualizer` 模式，将不同类型的绘图逻辑（如 AUC, Phidgets, Annotations）完全抽离出 `canvas.py`。

### E. 国际化 (I18N)
*   **现状**: 界面使用了 `QApplication.translate`，但单位目前硬编码为 `/min`。
*   **改进**: 完善多语言翻译文件，并根据用户设置动态显示温度单位 (°C/°F)。
