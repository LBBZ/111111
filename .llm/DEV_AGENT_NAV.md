# DEV_AGENT_NAV (Upload This File)

Last updated: 2026-03-18
Use case: This is the single file to upload for a coding agent.

## A. Development Goal
- Work as a coding/development agent for this repository.
- Prioritize safe, minimal, architecture-consistent changes.
- Avoid broad code scanning unless a task explicitly requires it.

## B. One-File Rule
- If only one file is provided to an external agent, provide this file.
- This file contains enough context to handle most implementation tasks.
- For local work, AGENT_TOTAL_RULE.md is the authoritative base; this file is the portable upload profile.

## C. Project Runtime Architecture
- Main package: DroneController
- Layers:
  - core: orchestration and loop
  - control: low-level motion
  - perception: sensors and image processing
  - infra: AirSim client integration
  - io: logs and artifact writing
  - workflow: task specs, per-task processor, workflow scheduler

## D. Dependency Direction
- Allowed:
  - core -> control/perception/io/infra
  - control -> infra
  - perception -> infra
  - io -> stdlib/local helpers
  - infra -> external libs
- Forbidden:
  - control/perception/io -> core
  - infra -> core/control/perception/io

## E. Core Module Map
- DroneController/core/controller.py
  - class DroneController
  - initialize_episode(start_pos_m, start_rot_deg) -> dict
  - run(max_steps=None, on_step_end=None, task_context=None) -> dict
- DroneController/core/motion_executor.py
  - class MotionExecutor
  - parse(action_json)
  - execute(parsed_action)
  - get_sensor_data()
  - build_prompt(sensor_data, task_context=None)
- DroneController/core/llm_interface.py
  - class LLMInterface (mock output source)

## F. Infra/Perception/Control Module Map
- DroneController/infra/airsim_client.py
  - class AirSimClientSingleton
- DroneController/control/drone_motion.py
  - class DroneMotion
- DroneController/perception/drone_camera.py
  - class DroneCamera
- DroneController/perception/image_processing.py
  - merge_images(...)
  - compress_image_to_size(...)
  - compute_depth_index(...)

## G. IO and Output Contracts
- DroneController/io/logger.py
  - class Logger
  - writes drone_log.txt + drone_log.json
- DroneController/io/artifact_writer.py
  - class WorkflowArtifactWriter
  - prepare_for_rerun(), write_json(), write_traj_csv(), save_step_visual()

Online workflow output path:
- task/<task_id>/
  - meta.json
  - results.json
  - traj.csv
  - plan.json
  - drone_log.txt
  - drone_log.json
  - step_visual/step_xxx/*

## H. Workflow Entrypoints
- Online single-case eval:
  - DroneController/run_vln_workflow_eval.py
  - args: --dataset_root, --task_root, --task_ids, --max_steps, --bootstrap_max_steps
  - always prepends a bootstrap_simple warm-up task using first task init pose
  - dispatch continues even if one task fails (including bootstrap)
- Offline fake eval:
  - DroneController/run_vln_eval_fake.py

## I. Metrics and Dataset Facts
- Metrics file: DroneController/vln_metrics.py
- Key symbols:
  - EpisodeGT
  - load_gt_episode(...)
  - compute_vln_metrics(...)
- Coordinate facts:
  - AirSim uses NED meters (X forward, Y right, Z down-positive)
  - move_up decreases z, move_down increases z
  - Datasets/vln/start_loc.txt positions are cm and must be divided by 100
  - workflow start z transform: z_m = -(z_cm / 100)
  - task metadata input is JSON-first: Datasets/vln/episode_index.json + Datasets/vln/groups.json, fallback to start_loc.txt

## J. Deprecated Imports (Do Not Use)
- DroneController.controller
- DroneController.motion_executor
- DroneController.llm_interface
- DroneController.drone_motion
- DroneController.drone_camera
- DroneController.image_processing
- DroneController.airsim_client
- DroneController.logger
- DroneController.artifact_writer

Use layered imports, e.g.:
- from DroneController.core.controller import DroneController
- from DroneController.io.artifact_writer import WorkflowArtifactWriter

## K. Validation Commands
- D:/Conda/envs/airsim/python.exe -m compileall DroneController
- D:/Conda/envs/airsim/python.exe -u DroneController/run_vln_workflow_eval.py --dataset_root Datasets/vln --task_root task --task_ids 0

## L. Change Playbooks
- Add new prompt field:
  1) edit core/motion_executor.py:get_sensor_data
  2) edit core/motion_executor.py:build_prompt
  3) if persisted, sync io/logger.py and plan/results schema
- Change artifact schema:
  1) edit io/artifact_writer.py
  2) edit run_vln_workflow_eval.py
  3) keep compatibility unless break requested
- Rename/move module:
  1) enforce dependency direction rules
  2) update imports in scripts/tests
  3) run compileall

## M. Markdown Maintenance Rule
- Any change to architecture/import direction/CLI/output schema/metric keys must update:
  1) .llm/AGENT_TOTAL_RULE.md first
  2) this file (DEV_AGENT_NAV.md)
- If conflict exists, AGENT_TOTAL_RULE.md is final authority.

## N. Recommended Upload Set
- Minimal: upload only this file.
- Local full context (optional): also keep AGENT_TOTAL_RULE.md available.
