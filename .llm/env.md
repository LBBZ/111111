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
