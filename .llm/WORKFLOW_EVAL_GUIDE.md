# Workflow Eval Guide for Development Agent

## Online Single-Case Entry
- Script: DroneController/run_vln_workflow_eval.py
- Args:
  - --dataset_root (default Datasets/vln)
  - --task_root (default task)
  - --task_ids (required task sequence, e.g. 1 2 3; single task uses one id)
  - --max_steps (default 200)
  - --bootstrap_max_steps (default 5)

## Runtime Flow
1. `WorkflowManager` runs a bootstrap task first (init pose from first task id).
2. Dispatch each task id sequentially; one failure does not stop remaining tasks.
3. `TaskProcessor` runs controller loop and persists artifacts.
4. Compute SR/NE/SPL via DroneController/vln_metrics.py for normal VLN tasks.

## Output Files
- task/console.log
- task/error.log
- task/workflow_summary.json
- task/bootstrap/meta.json
- task/bootstrap/lifecycle.jsonl
- task/<task_id>/meta.json
- task/<task_id>/lifecycle.jsonl
- task/<task_id>/drone_log.txt
- task/<task_id>/drone_log.json
- task/<task_id>/results.json / traj.csv / plan.json (if run reaches those stages)

## Overwrite Behavior
- Rerun same output directory replaces stale step visuals and lifecycle logs.
- No episodes/<idx> nesting in online workflow.

## Validation Commands
- Compile package:
  - D:/Conda/envs/airsim/python.exe -m compileall DroneController
- Run workflow:
  - D:/Conda/envs/airsim/python.exe -u DroneController/run_vln_workflow_eval.py --dataset_root Datasets/vln --task_root task --task_ids 0
