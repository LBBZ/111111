# Workflow Evaluation Integration - Detailed Execution Spec

Last updated: 2026-03-15
Audience: handoff document for another coding agent
Priority: must follow exactly unless explicitly changed by user

## 1) Objective and Success Definition

### Primary objective
Integrate evaluation into the online DroneController workflow for exactly one dataset case per run, with deterministic artifact layout for downstream automation and review.

### Definition of success
One execution of the new entry script produces one task directory with flat outputs and local logs:
- task/<task_id>/meta.json
- task/<task_id>/results.json
- task/<task_id>/traj.csv
- task/<task_id>/plan.json
- task/<task_id>/drone_log.txt
- task/<task_id>/drone_log.jsonl

No episodes/<id>/ nesting is allowed in this new workflow.

## 2) Locked Requirements (Already Agreed)

These are fixed constraints, not proposals:

1. One run maps to one dataset case id.
2. task_id equals dataset case id for this workflow entry.
3. Output root is flat under task/<task_id>/.
4. Logs must be written into the same task/<task_id>/ folder.
5. Re-running same task_id must overwrite previous output files.
6. Keep mock model interaction path (LLMInterface remains simulated).
7. New entry script must not expose these options:
- --episodes
- --success_radius
- --fail_fast
8. Do not regenerate previously removed refactor-note docs unless user asks again.

## 3) Current Baseline (Important for Implementation)

### Current logger behavior
File: DroneController/logger.py
- Logger currently takes txt_file/json_file only.
- It appends logs and has no output_dir abstraction.
- It writes to root-level files by default.

### Current controller behavior
File: DroneController/controller.py
- DroneController currently builds Logger(log_filename) only.
- run() loops until parsed type is done.
- It logs per-step prompt/output/parsed_action/state.
- It does not currently expose a ready-to-save run artifact bundle for traj/plan writers.

### Current fake evaluator behavior
File: DroneController/run_vln_eval_fake.py
- Batch-oriented interface exists.
- Uses --episodes and --success_radius.
- Writes nested outputs under task/<task_id>/episodes/<idx>/...
- This is now legacy/offline reference behavior.

## 4) Scope and Out-of-Scope

### In scope
1. Logger enhancement for task-local logging.
2. Controller enhancement for task-local logger wiring and run artifact exposure.
3. New single-case online workflow entry script.
4. Metric computation integration using existing vln_metrics utilities.
5. Flat output writing under task/<task_id>/.

### Out of scope
1. Motion-policy redesign.
2. Real model integration replacing mock LLM.
3. Dataset format changes.
4. Broad refactor outside listed files.

## 5) Target File Changes (Exact Plan)

## 5.1 Logger upgrade

Target file:
- DroneController/logger.py

Required changes:
1. Extend constructor to support optional output_dir and overwrite.
2. Resolve final log paths as:
- output_dir/drone_log.txt
- output_dir/drone_log.jsonl
3. Preserve backward compatibility:
- If output_dir is None, old behavior still works.
4. Overwrite semantics:
- If overwrite=True, truncate both files in __init__.
- Runtime log() still appends entries after initialization.

Recommended signature:
- Logger(txt_file="drone_log.txt", json_file="drone_log.jsonl", output_dir=None, overwrite=True)

Implementation caution:
- Current log() uses prompt_dict in jsonl payload; ensure prompt_dict is always defined even when prompt JSON parsing fails.

## 5.2 Controller upgrade

Target file:
- DroneController/controller.py

Required changes:
1. Add output_dir parameter in DroneController initialization.
2. Initialize Logger with output_dir so logs are task-local.
3. Capture and expose run artifacts needed by evaluator writer:
- predicted trajectory points per step
- per-step plan/action record
- terminal status (done or forced stop)
4. Keep existing execution flow unchanged:
- get sensor data
- build prompt
- call llm
- parse
- execute
- log
- stop on done

Recommended run output contract (Python object returned by run):
- trajectory: list of [x, y, z]
- plan_steps: list of dict
- status: dict with done/step_count/end_reason

## 5.3 New workflow entry

Target file:
- DroneController/run_vln_workflow_eval.py (new)

CLI contract (only these):
1. --dataset_root, default Datasets/vln
2. --task_root, default task
3. --task_id, required int

Workflow responsibilities:
1. Resolve output_dir = task_root/task_id.
2. Ensure overwrite behavior for reruns.
3. Load GT episode with vln_metrics.load_gt_episode(dataset_root, task_id).
4. Run controller for this single case and collect trajectory/plan.
5. Compute SR/NE/SPL using existing vln_metrics compute utilities.
6. Write all required flat outputs.
7. Print concise terminal summary for human check.

Must not exist in this script:
1. --episodes
2. --success_radius
3. --fail_fast

## 5.4 Fake evaluator status

Target file:
- DroneController/run_vln_eval_fake.py

Action:
- Keep as legacy offline utility.
- Optional header comment to prevent confusion with new online single-case entry.

## 6) Output File Schemas (Concrete)

## 6.1 meta.json

Minimum required fields:
1. task_id: int
2. dataset_root: string
3. started_at: string
4. finished_at: string
5. controller_mode: "online_airsim_mock_llm"
6. script: "DroneController/run_vln_workflow_eval.py"

## 6.2 results.json

Minimum required fields:
1. task_id: int
2. success: 0 or 1
3. ne: float
4. spl: float
5. sr: float
6. path_length_pred: float
7. path_length_gt: float
8. steps: int
9. end_reason: string

## 6.3 traj.csv

Header:
- step,x,y,z

Rows:
- one row per recorded step position

## 6.4 plan.json

Array of step records, each with:
1. step
2. raw_model_output
3. parsed_action
4. execute_status
5. drone_state_after

## 7) Overwrite Policy (Strict)

For a rerun on the same task_id:
1. Required files are replaced with fresh content.
2. No duplicate suffix files like results(1).json.
3. No stale nested episodes directory created by new workflow.

Recommended implementation:
1. Create output_dir if missing.
2. For each required file path, write with mode="w".
3. Logger initializes with overwrite=True to truncate log files at start.

## 8) Validation and Acceptance Matrix

## 8.1 Static checks
1. New script exists: DroneController/run_vln_workflow_eval.py
2. Script argparse options contain only dataset_root/task_root/task_id plus optional seed/debug if user approves.
3. Script does not parse --episodes/--success_radius/--fail_fast.
4. Logger supports output_dir and overwrite.

## 8.2 Runtime checks
Run from workspace root:

python -u DroneController/run_vln_workflow_eval.py --dataset_root Datasets/vln --task_root task --task_id 0

Expected after run:
1. task/0/meta.json exists.
2. task/0/results.json exists and contains SR/NE/SPL fields.
3. task/0/traj.csv exists and has header + rows.
4. task/0/plan.json exists and has step records.
5. task/0/drone_log.txt exists.
6. task/0/drone_log.jsonl exists.
7. No task/0/episodes/ directory created by this workflow.

## 8.3 Rerun checks
Run same command again with task_id 0:
1. File timestamps update.
2. File content is replaced, not appended across runs except within one run log lifecycle.
3. Directory remains flat and clean.

## 9) Risk Notes and Mitigations

1. AirSim availability risk:
- If AirSim is not running, online run may fail.
- Mitigation: fail fast with clear error, still preserve partial meta if useful.

2. Infinite/long loop risk in controller:
- If model never outputs done, run may continue too long.
- Mitigation: add conservative max_steps guard in new workflow script or controller (documented if added).

3. Prompt parsing risk in logger:
- Invalid prompt JSON currently can break json_entry if prompt_dict undefined.
- Mitigation: initialize prompt_dict safely in exception path.

## 10) Recommended Implementation Order

1. Modify DroneController/logger.py.
2. Modify DroneController/controller.py.
3. Create DroneController/run_vln_workflow_eval.py.
4. Optional note update in DroneController/run_vln_eval_fake.py.
5. Run smoke test and verify artifacts.

## 11) Done Criteria (Final Gate)

All must be true:
1. Single-case workflow entry exists and runs with task_id.
2. Outputs are flat under task/<task_id>/.
3. Logs are task-local under task/<task_id>/.
4. Rerun with same task_id overwrites output files.
5. New workflow entry does not expose episodes/success_radius/fail_fast.
6. SR/NE/SPL is written to results.json.

## 12) Notes for Next Agent

1. Treat this document as execution contract, not brainstorming.
2. Keep edits minimal and localized to listed files.
3. Preserve existing behavior unless required by locked constraints.
4. If conflicting old docs are found, follow this file and latest user decisions.
