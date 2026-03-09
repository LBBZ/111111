# Drone Navigation Environment

Environment specification for the drone navigation agent running in **AirSim + EmbodiedCity**.

This file describes the **world model, dataset format, and evaluation metrics**.

---

# Coordinate System

AirSim uses **NED coordinates (meters)**.

```
X : forward
Y : right
Z : down (positive)
```

Important:

```
move_up(d)   -> z -= d
move_down(d) -> z += d
```

---

# World Origin

The drone origin is reset by AirSim settings.

File:

```
others/settings.json
```

The initial spawn location becomes the drone's `(0,0,0)`.

Do NOT assume a fixed global origin.

---

# Unit Conversion

Some dataset coordinates are in **Unreal centimeters**.

Convert before use:

```
meters = cm / 100
```

---

# Project Structure

Two stacks exist.

### Primary stack

```
DroneController/
```

Used for:

```
drone control
camera observations
trajectory execution
evaluation
```

Main modules:

```
DroneCamera
DroneMotion
airsim_client
vln_metrics
```

---

### Reference stack (benchmark only)

```
embodied_vln.py
prompts/
Datasets/vln/
```

Used only for:

```
dataset format
evaluation alignment
```

Do NOT use its control pipeline.

---

# Dataset

Location:

```
Datasets/vln/
```

Files:

```
start_loc.txt
label/*.csv
```

Definitions:

```
start_pos_m
target_pos_m
gt_path_len_m
```

Computation:

```
target_pos_m = start_pos_m + rel[-1]
```

Where:

```
rel = relative displacements from label csv
```

---

# Evaluation Metrics

Implemented in:

```
DroneController/vln_metrics.py
```

Given predicted trajectory:

```
pred_positions_m = [(x, y, z), ...]
```

Metrics:

```
NE   = distance(final_pred_pos, target_pos_m)

SR   = 1 if NE < 20m else 0

SPL  = SR * (gt_path_len_m / max(gt_path_len_m, pred_len_m))
```

Goal:

```
minimize NE
maximize SR
maximize SPL
```

---

# Task Artifacts and Offline Evaluation

Each evaluation run writes artifacts under:

```
task/<task_id>/
```

Structure:

```
task/<task_id>/meta.json
task/<task_id>/results.json
task/<task_id>/episodes/0/{plan.json,traj.csv,images/}
task/<task_id>/episodes/1/{...}
task/<task_id>/episodes/2/{...}
```

- `meta.json` records:

```
task_id
created_at
dataset_root        # usually "Datasets/vln"
episodes            # e.g. [0,1,2]
success_radius_m    # usually 20.0
```

- `traj.csv` is the predicted trajectory in world/NED coordinates, one row per step.
- `results.json` contains:

```
meta      # copy of meta.json info
episodes  # per-episode GT, prediction and metrics
summary   # mean SR/NE/SPL over all evaluated episodes
```

There is also a helper script for **offline smoke testing** (no AirSim, no LLM):

```
DroneController/run_vln_eval_fake.py
```

It:

1. Reads GT for a few episodes from `Datasets/vln`.
2. Generates fake trajectories (high / medium / fail).
3. Writes `task/<task_id>/episodes/<idx>/traj.csv` and `plan.json`.
4. Calls `DroneController/vln_metrics.py` to compute SR/NE/SPL.
5. Produces `task/<task_id>/results.json` with per-episode metrics and a summary.

---

# Common Pitfalls

Camera naming mismatch:

```
DroneController -> Front/Back/.../TopDown
VLN code       -> "0" / "3"
```

Do NOT mix them.

---

Vehicle name must match AirSim settings:

```
others/settings.json
DefaultVehicle = "keli"
```

---

Dataset path is case sensitive:

```
Datasets/
NOT dataset/
```

---

Remember:

```
AirSim Z axis points downward
```
