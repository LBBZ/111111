# Drone Navigation Agent Context

This file defines the **environment, interfaces, and rules** for the drone navigation agent running in **AirSim + EmbodiedCity**.

The agent receives observations and outputs the **next action** for the drone.

---

# 1. Environment

## Coordinate System

AirSim uses **NED (meters)**:

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

## World Origin

The drone origin is **reset by AirSim settings**.

File:

```
others/settings.json
```

The initial spawn location becomes the drone's `(0,0,0)`.

Do NOT assume global origin is fixed.

---

## Unit Conversion

Some dataset coordinates are **Unreal centimeters**.

Convert:

```
meters = cm / 100
```

---

# 2. Project Structure

Two code stacks exist.

### Primary (use this)

```
DroneController/
```

Provides:

* drone control
* camera observations
* trajectory execution
* evaluation

Key modules:

```
DroneCamera
DroneMotion
airsim_client (singleton)
vln_metrics
```

---

### Reference Only

Original benchmark code:

```
embodied_vln.py
prompts/
Datasets/vln/
```

Used only for:

* dataset
* evaluation alignment

Do NOT use its control pipeline.

---

# 3. Observation Interface

From:

```
DroneController/DroneCamera
```

Nine camera directions:

```
Front
Back
Left
Right
FrontLeft
FrontRight
BackLeft
BackRight
TopDown
```

Each view provides:

```
RGB image
Depth image
Depth NPY (float32 meters)
```

---

# 4. Action Interface

From:

```
DroneController/drone_motion.py
```

### Translation (meters)

```
move_forward(d)
move_backward(d)

move_left(d)
move_right(d)

move_up(d)
move_down(d)
```

### Rotation (degrees)

```
turn_left(angle_deg)
turn_right(angle_deg)
```

---

## Action Constraints

Each step must output **ONE action only**.

Recommended ranges:

```
translation: 5–10 meters
rotation:    10–45 degrees
```

---

# 5. Navigation Loop

For each step:

1. receive observations (9 views)
2. receive task instruction
3. receive current pose
4. optionally receive history

Agent must:

```
understand environment
estimate navigable direction
progress toward goal
output next action
```

Only **one step** is generated each time.

---

# 6. Dataset

Location:

```
Datasets/vln/
```

Files:

```
start_loc.txt       # start index, Unreal-world position (cm), rotation, instruction
label/*.csv         # per-episode relative displacements (meters) from the start
```

Definitions (as implemented in `DroneController/vln_metrics.py`):

```
start_pos_m    # start position in meters (cm / 100 from start_loc)
target_pos_m   # start_pos_m + final relative offset from label/*.csv
gt_path_len_m  # sum of Euclidean distances along the GT relative trajectory
```

Target position:

```
target_pos_m = start_pos_m + rel[-1]
```

---

# 7. Evaluation Metrics

Implemented in:

```
DroneController/vln_metrics.py
```

Given a GT episode (parsed from `Datasets/vln`) and a predicted trajectory
`pred_positions_m = [(x, y, z), ...]` in the AirSim world frame (meters), we compute:

```
NE   = ||final_pred_pos - target_pos_m||_2
SR   = 1 if NE < success_radius_m (default: 20.0) else 0
SPL  = SR * (gt_path_len_m / max(gt_path_len_m, pred_len_m))
```

Goal:

```
minimize NE
maximize SR
maximize SPL
```

---

# 8. Common Pitfalls

Camera naming:

```
DroneController -> Front/Back/.../TopDown   (defined in others/settings.json)
VLN code       -> "0" / "3"                 (used by original AirsimAgent)
```

Do NOT mix them.

---

Vehicle name must match AirSim settings:

```
DefaultVehicle in others/settings.json -> "keli"
DroneController.*                      -> vehicle_name="keli"
```

---

Dataset path case:

```
Datasets/
NOT dataset/
```

---

Remember:

```
AirSim Z axis points downward (NED)
move_up(d)   -> z -= d
move_down(d) -> z += d
```

---

# 9. Required Output Format

Each step must output JSON:

```json
{
  "action": "move_forward",
  "value": 8.0,
  "reason": "front path is clear and consistent with the language instruction, so moving forward reduces distance to the goal"
}
```

Stop action:

```json
{
  "action": "stop",
  "reason": "the drone is already close enough to the target region; further motion brings limited benefit"
}
```

Rules:

```
one action per step
valid action name only
```

---

# 10. Quick Start (for implementers)

- **Environment check**
  - Use `DroneController/airsim_client.py` to create the AirSim client, confirm connection, arm and take off.
- **Multi-view observation sanity check**
  - Run `DroneController/init_img.py` and call `capture_views_at_pose(x, y, z, yaw_deg)` to verify 9-direction RGB/Depth outputs.
- **Motion + logging sanity check**
  - Run `DroneController/test_runner.py` to execute a random action sequence, inspect logged positions and saved images.
- **Metric integration**
  - Record predicted trajectories in meters (AirSim world frame) and feed them into `DroneController/vln_metrics.py.compute_vln_metrics` to compute SR/NE/SPL.
