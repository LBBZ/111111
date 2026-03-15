# Workflow Eval Guide for Development Agent

## Online Single-Case Entry
- Script: DroneController/run_vln_workflow_eval.py
- Args:
  - --dataset_root (default Datasets/vln)
  - --task_root (default task)
  - --task_id (required)

## Runtime Flow
1. Load GT episode from Datasets/vln.
2. Run DroneController.core.controller loop.
3. Persist outputs via DroneController.io.artifact_writer.
4. Compute SR/NE/SPL via DroneController/vln_metrics.py.

## Required Output Files
- task/<task_id>/meta.json
- task/<task_id>/results.json
- task/<task_id>/traj.csv
- task/<task_id>/plan.json
- task/<task_id>/drone_log.txt
- task/<task_id>/drone_log.json

## Overwrite Behavior
- Rerun same task_id must replace files.
- No episodes/<idx> nesting in online workflow.

## Validation Commands
- Compile package:
  - D:/Conda/envs/airsim/python.exe -m compileall DroneController
- Run workflow:
  - D:/Conda/envs/airsim/python.exe -u DroneController/run_vln_workflow_eval.py --dataset_root Datasets/vln --task_root task --task_id 0
