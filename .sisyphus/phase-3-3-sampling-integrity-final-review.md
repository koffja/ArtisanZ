# Phase 3.3 Sampling Integrity Final Review

审查日期：2026-07-24
范围：deferred 输入恢复、锁失败重试、generation、shutdown、stale 结果、新旧批次顺序。
未扩展到输入滤波、RoR、PID、报警或绘图。

## 结论

**PASS**

## 审查结果

### deferred retry

- `_schedule_deferred_sample_resume()` 使用 `_deferred_sample_retry_scheduled` 合并 retry，最多保持一个排程中的 10ms `QTimer.singleShot`。
- `_resume_deferred_sample_input()` 在 retry 前检查批次存在、generation 一致、worker 未关闭；失效批次直接丢弃。
- `sample_processing()` 在 `profileDataSemaphore` 获取失败时不清除 `deferred_batch`，仅对仍占用槽位的同一对象安排 retry。
- 锁成功后才清除同一 deferred 对象；成功处理与 `_finalize_sample_processing()` 都会触发下一批次恢复。

### 批次顺序与去重

- worker 忙碌时只保留最新输入，并复制 ET/BT/时间列表，避免设备回调修改 deferred 数据。
- 恢复旧批次时，新到输入先进入 deferred 槽位；旧批次锁失败会继续重试，锁成功后由 finalize 恢复最新批次。
- retry 回调不会主动复制消费同一批次；槽位身份检查阻止旧批次清除或重入新批次。

### generation、stale、shutdown

- `_invalidate_processed_frame_work()` 先递增 generation，再清除 pending/deferred，并取消 retry 状态；reset、clear measurements、停止录制、停止监控、shutdown 路径均调用它。
- `_processed_frame_result_ready()` 与 `_processed_frame_error()` 同时检查 pending、sequence、generation、shutdown；reset 或停止后的旧 worker 结果不会写入新状态。
- shutdown 在 invalidation 后设置关闭标记；线程等待超时后继续等待完成，不销毁仍运行的 `QThread`。

## 验证

- `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_processed_frame_worker.py test/unitary/artisanlib/test_sample_processing.py test/unitary/artisanlib/test_canvas_renderer_selection.py -q`
  - `157 passed, 2 warnings`
- `.venv/bin/python -m py_compile artisanlib/canvas.py artisanlib/main.py artisanlib/processed_frame_worker.py`：通过。
- `.venv/bin/python -m ruff check artisanlib/canvas.py artisanlib/processed_frame_worker.py test/unitary/artisanlib/test_processed_frame_worker.py`：通过。
- `git diff --check`：通过。

## 结论与边界

Phase 3.3 sampling-integrity 通过最终复审。未提交。
最新值合并策略保证 worker 忙碌期间不滞留旧 backlog，但不承诺保留每一个高频采样点；后续 Phase 3.3-B 迁移平滑、纯 RoR 与 PID process-value 前，仍需做 1 Hz、5 Hz、10 Hz 差分与完整性验证。
