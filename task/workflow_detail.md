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
- 2026-03-18 15:58:31 START task_id=bootstrap kind=bootstrap_simple
- 2026-03-18 15:58:52 END task_id=bootstrap status=OK end_reason=done
- 2026-03-18 15:58:52 START task_id=2 kind=vln
- 2026-03-18 16:00:08 END task_id=2 status=OK end_reason=done
