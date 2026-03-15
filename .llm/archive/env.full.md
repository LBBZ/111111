# Drone Navigation Environment (Refactored)

This file summarizes the runtime environment, data format, metrics, and execution entry points after refactoring.
It is designed for fast agent onboarding with minimal context cost.

---

# 1. Runtime Environment

## 1.1 Simulation stack

- AirSim + EmbodiedCity scene
- Primary Python control pipeline in `DroneController/`

## 1.2 Key AirSim configuration

Config file: `others/settings.json`

- `DefaultVehicle`: `keli`
- 9 cameras are defined: Front/Back/Left/Right/FrontLeft/FrontRight/BackLeft/BackRight/TopDown
- Initial pose is set by settings; do not hardcode a global origin in logic

---

# 2. Coordinates and Units

## 2.1 AirSim coordinates

AirSim uses NED in meters:

- X: forward
- Y: right
- Z: down is positive

Therefore:

- `move_up(d)` -> `z` decreases
- `move_down(d)` -> `z` increases

## 2.2 Dataset coordinates

`Datasets/vln/start_loc.txt` stores start position in Unreal centimeters:

`meters = cm / 100`

`Datasets/vln/label/<idx>.csv` stores relative trajectory displacements in meters.

---

# 3. Architecture and Responsibility Boundaries

## 3.1 Primary execution stack (recommended)

`DroneController/`

- `controller.py`: main loop
- `motion_executor.py`: action parsing and execution bridge
- `drone_camera.py`: RGB/Depth/Seg observation capture
- `drone_motion.py`: flight actions (translation/rotation/teleport)
- `vln_metrics.py`: SR/NE/SPL computation
- `run_vln_eval_fake.py`: offline evaluation smoke test without AirSim

## 3.2 Reference stack (alignment/compatibility)

`embodied_vln.py`, `vln/`, `prompts/`, `Datasets/vln/`

Use this stack for benchmark alignment and dataset compatibility, not as the primary online control entry.

---

# 4. VLN Dataset Format

Root: `Datasets/vln/`

- `start_loc.txt`
- `label/<idx>.csv`

In `vln_metrics.load_gt_episode()`:

1. Parse `start_pos_m`, `start_yaw_deg`, and `instruction`
2. Read relative trajectory `rel` from `label/<idx>.csv`
3. Compute goal: `target_pos_m = start_pos_m + rel[-1]`
4. Compute GT path length: `gt_path_len_m`

---

# 5. Metric Definitions (SR / NE / SPL)

Implementation: `DroneController/vln_metrics.py`

Given predicted absolute trajectory `pred_positions_m = [(x,y,z), ...]`:

- $NE = ||p_{final} - p_{goal}||_2$
- $SR = \mathbb{1}[NE < r]$, default $r=20m$
- $SPL = SR \cdot \frac{L}{\max(L, P)}$

Where:

- $L$: GT path length `gt_path_len_m`
- $P$: predicted path length `pred_len_m`

---

# 6. Task Artifact Layout

Unified output root: `task/<task_id>/`

Typical structure:

```text
task/<task_id>/
  meta.json
  results.json
  episodes/
    <idx>/
      traj.csv
      plan.json
      images/
```

Field summary:

- `meta.json`: dataset root, episode list, success radius, timestamps
- `traj.csv`: predicted position per step (world/NED, meters)
- `plan.json`: per-step plan/action information
- `results.json`: per-episode metrics + aggregated summary

---

# 7. Practical Entry Points

## 7.1 Online control loop (AirSim required)

- `DroneController/test/workflow_test.py`

Triggers: observation capture -> LLM interface -> action execution -> logging.

## 7.2 Offline evaluation smoke test (AirSim not required)

- `DroneController/run_vln_eval_fake.py`

It will:

1. Load GT from `Datasets/vln`
2. Generate fake trajectories (`hi`/`mid`/`fail`)
3. Write `traj.csv` and `plan.json`
4. Compute SR/NE/SPL
5. Write `results.json`

Common args:

- `--dataset_root` (default `Datasets/vln`)
- `--out_root` (default `task`)
- `--task_id`
- `--episodes 0 1 2`
- `--success_radius 20.0`

---

# 8. Common Pitfalls

1. Do not mix current camera names with older VLN camera indexing.
2. Keep vehicle name aligned with settings (`DefaultVehicle = keli`).
3. Use `Datasets/vln` path exactly, not `dataset/vln`.
4. Always convert start positions in `start_loc.txt` from cm to m.
5. Current `LLMInterface` returns mock outputs for pipeline validation, not production model calls.
