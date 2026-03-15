# Development Agent Total Rule

Last updated: 2026-03-15
Status: SINGLE SOURCE OF TRUTH FOR CODING AGENTS
Usage: Import this file only for normal development tasks.

## 1) Scope and Goal
- This file is for software development agents working on this repo.
- It is not a policy prompt for navigation reasoning.
- Objective: provide enough concrete project knowledge so the agent can implement most tasks without broad codebase re-reading.

## 2) Workspace Snapshot
- Main runtime package: DroneController/
- Key related roots:
  - Datasets/vln (GT source)
  - task/<task_id> (evaluation outputs)
  - DroneController/test (online test scripts and artifacts)
  - others/settings.json (AirSim config)

## 3) Layered Architecture (Authoritative)
- core/
  - controller.py
  - motion_executor.py
  - llm_interface.py
- control/
  - drone_motion.py
- perception/
  - drone_camera.py
  - image_processing.py
- infra/
  - airsim_client.py
- io/
  - logger.py
  - artifact_writer.py
- top-level runtime scripts:
  - run_vln_workflow_eval.py (online single-case)
  - run_vln_eval_fake.py (legacy/offline fake eval)
  - vln_metrics.py (metrics and GT loader)

## 4) Import Direction Rules
- Allowed directions:
  - core -> control/perception/io/infra
  - control -> infra
  - perception -> infra
  - io -> stdlib and local helpers only
  - infra -> external libs only
- Forbidden directions:
  - control/perception/io -> core
  - infra -> core/control/perception/io

## 5) Deprecated Imports (Do Not Reintroduce)
- Removed flat module imports:
  - DroneController.controller
  - DroneController.motion_executor
  - DroneController.llm_interface
  - DroneController.drone_motion
  - DroneController.drone_camera
  - DroneController.image_processing
  - DroneController.airsim_client
  - DroneController.logger
  - DroneController.artifact_writer

Use layered imports instead, for example:
- from DroneController.core.controller import DroneController
- from DroneController.io.artifact_writer import WorkflowArtifactWriter

## 6) Runtime Contracts (Important)

### 6.1 core.controller.DroneController
- Constructor:
  - DroneController(executor=None, log_filename="drone_log.txt", output_dir=None, overwrite_logs=True)
- Main method:
  - run(max_steps=None, on_step_end=None) -> dict
- Return contract:
  - {
    "trajectory": [[x,y,z], ...],
    "plan_steps": [
      {
        "step": int,
        "raw_model_output": dict,
        "parsed_action": dict,
        "execute_status": str,
        "drone_state_after": dict
      }
    ],
    "status": {
      "done": bool,
      "step_count": int,
      "end_reason": "done|max_steps|unknown"
    }
  }

### 6.2 core.motion_executor.MotionExecutor
- parse(action_json) -> dict
  - supports motion json and done json.
- execute(parsed_action) -> "ok" | "done"
- get_sensor_data() -> dict with keys:
  - mosaic_image
  - rgb_views
  - depth_maps
  - depth_summary
  - drone_state
- build_prompt(sensor_data) -> json string
  - current image field is placeholder string.

### 6.3 io.logger.Logger
- Writes:
  - drone_log.txt (human-readable append during run)
  - drone_log.json (formatted JSON array)
- overwrite=True truncates at run start.

### 6.4 io.artifact_writer.WorkflowArtifactWriter
- prepare_for_rerun(): cleans legacy episodes/ and stale outputs.
- write_json(name, obj)
- write_traj_csv(name, positions)
- save_step_visual(step_idx, sensor_data, camera)

## 7) Online Workflow Script Contract
- Script: DroneController/run_vln_workflow_eval.py
- CLI (only):
  - --dataset_root (default Datasets/vln)
  - --task_root (default task)
  - --task_id (required int)
- Behavior:
  - one run = one dataset case id
  - task_id == dataset case id
  - flat outputs under task/<task_id>/

Required files under task/<task_id>/:
- meta.json
- results.json
- traj.csv
- plan.json
- drone_log.txt
- drone_log.json
- step_visual/step_xxx/... (if run path includes visual saving callback)

## 8) Metrics Contract (vln_metrics.py)
- compute_vln_metrics(gt, pred_positions_m, success_radius_m=20.0)
- Returns keys:
  - SR, NE, SPL
  - pred_len_m, gt_len_m
  - success_radius_m
- Definitions:
  - NE = distance(final, goal)
  - SR = 1[NE < success_radius]
  - SPL = SR * (L / max(L, P))

## 9) Data and Coordinate Facts
- AirSim is NED in meters:
  - X forward, Y right, Z down-positive
- move_up decreases z; move_down increases z.
- Datasets/vln/start_loc.txt stores cm; convert by /100.
- Vehicle name expected in runtime settings: keli.

## 10) Known Runtime Caveats
- AirSim/msgpack RPC may occasionally throw tornado/assertion/transport errors.
- Do not run multiple heavy AirSim control scripts concurrently in one simulation session.
- If workflow hangs in turning loop, check simulator state and connection health before code-level changes.

## 11) Standard Validation Commands
- Compile package:
  - D:/Conda/envs/airsim/python.exe -m compileall DroneController
- Run online workflow:
  - D:/Conda/envs/airsim/python.exe -u DroneController/run_vln_workflow_eval.py --dataset_root Datasets/vln --task_root task --task_id 0
- Basic output check target:
  - task/0/results.json exists

## 12) Change Playbooks (Use Without Re-reading Full Code)

### 12.1 Add new sensor-derived field into prompt
1. Edit core/motion_executor.py:get_sensor_data.
2. Add field into build_prompt payload.
3. If persisted, extend logger entry and plan/output schema carefully.
4. Update section 6 here.

### 12.2 Change artifact schema
1. Edit io/artifact_writer.py.
2. Edit run_vln_workflow_eval.py write path.
3. Keep backward compatibility unless explicitly breaking.
4. Update sections 7 and 14 here.

### 12.3 Move/rename modules
1. Keep layer rules in section 4.
2. Update imports in scripts/tests.
3. Run compileall.
4. Update sections 3/4/5 here.

## 13) Editing Policy for Agents
- Prefer minimal, localized edits.
- Avoid unrelated refactors.
- Preserve CLI and file schema unless requested.
- If a breaking change is required, state impact explicitly in final response.

## 14) Markdown Governance (Mandatory)
- Trigger to update this file:
  - module path changes
  - import direction changes
  - workflow CLI changes
  - artifact schema changes
  - metric key changes
  - new core runtime entry points
- Required update steps:
  1. Update this file first.
  2. Update Last updated.
  3. Add one line in change log.
  4. Sync optional support docs in .llm/.

## 15) Optional Supporting Docs
- .llm/PROJECT_STRUCTURE.md
- .llm/WORKFLOW_EVAL_GUIDE.md
- .llm/IMPORT_RULES.md

These are supplementary only. This file remains authoritative.

## 16) Change Log
- 2026-03-15: Established single-source development-agent rule file for .llm.
- 2026-03-15: Expanded to executable handbook level (interfaces, schemas, commands, playbooks).
