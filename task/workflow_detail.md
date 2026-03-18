# 任务流详细日志

## 本次运行将保存的文件
- meta.json: 任务元信息（初始化、时间戳、错误）
- plan.json: 每步动作计划
- traj.csv: 轨迹点
- results.json: 指标和终止原因
- lifecycle.jsonl: 生命周期阶段日志
- drone_log.txt / drone_log.json: 控制器详细日志
- step_visual/: 每步图像和深度快照

## 运行事件
- 2026-03-18 14:59:22 START task_id=bootstrap kind=bootstrap_simple
- 2026-03-18 14:59:53 END task_id=bootstrap status=FAILED end_reason=error
- 2026-03-18 14:59:53 START task_id=2 kind=vln
- 2026-03-18 15:00:27 END task_id=2 status=FAILED end_reason=error
