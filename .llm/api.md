# Drone Navigation Agent API (Refactored)

This file is a fast, high-signal reference for a new agent.
It describes the current DroneController pipeline, not the old direct embodied_vln flow.

---

# 1. Main Interaction Loop

Current online control loop:

1. `MotionExecutor.get_sensor_data()` collects observations.
2. `MotionExecutor.build_prompt()` builds the LLM prompt.
3. `LLMInterface.get_action(prompt)` returns action JSON.
4. `MotionExecutor.parse(action_json)` parses the JSON.
5. `MotionExecutor.execute(parsed_action)` executes via `DroneMotion`.
6. `Logger.log(...)` writes step logs.

Entry point: `DroneController/controller.py` -> `DroneController.run()`.

---

# 2. Observation Interface (Agent-visible)

Observation sources: `DroneController/drone_camera.py` + `DroneController/drone_motion.py`

## 2.1 Camera Names (9 views)

`Front`, `Back`, `Left`, `Right`, `FrontLeft`, `FrontRight`, `BackLeft`, `BackRight`, `TopDown`

## 2.2 Available Modalities

- RGB: `capture_all()` -> `Dict[str, np.ndarray(H,W,3)]`
- Depth: `capture_all_depth()` -> `Dict[str, np.ndarray(H,W,float32)]` in meters
- Segmentation: `capture_all_seg()` currently returns 5 views (Front/Back/Left/Right/TopDown)

## 2.3 Current Prompt Payload to LLM

`build_prompt()` currently returns a JSON string with this shape:

```json
{
  "image": "<base64 placeholder>",
  "depth_summary": {
    "front": 3.1,
    "left": 6.8,
    "topdown": 12.4,
    "right": 2.7,
    "back": 9.5
  },
  "drone_state": {
    "x": 7400.66,
    "y": -3555.18,
    "z": -53.36,
    "pitch": 0.0,
    "roll": 0.0,
    "yaw": 3.14
  }
}
```

Note: `image` is still a placeholder, not real base64 image data.

---

# 3. Action Output Protocol (Required)

Parser location: `DroneController/motion_executor.py`
It accepts only two JSON types.

## 3.1 Motion Action JSON

```json
{
  "turn_direction": "left|right|none",
  "turn_angle_deg": 18.0,
  "forward_distance": 2.5,
  "vertical_movement": 0.2,
  "notes": "optional"
}
```

Execution semantics:

- `turn_direction + turn_angle_deg`: rotate first (degrees)
- `forward_distance`: then move forward in body heading (meters)
- `vertical_movement`: finally move vertically (meters)
  - `> 0`: up
  - `< 0`: down

## 3.2 Task-complete JSON

```json
{
  "done": true,
  "message": "Mission completed.",
  "target_location_direction": "front-left"
}
```

Important: old format like `{"action":"move_forward","value":...}` is not directly executed by the current parser.

---

# 4. Low-level Motion Capabilities

Provided by `DroneController/drone_motion.py`:

- Translation: `move_forward/backward/left/right/up/down(d)` in meters
- Rotation: `turn_left/right(angle_deg)` in degrees
- Teleport: `teleport(x, y, z, yaw_rad)`

Execution order is fixed: rotate -> forward -> vertical.

---

# 5. Logs and Artifacts

## 5.1 Online control logs

`DroneController/controller.py` logs per step:

- prompt
- llm_output
- parsed_action
- execution_status
- drone_state
- depth_summary

Default logger writes txt + jsonl files.

## 5.2 VLN evaluation artifacts (offline/batch)

Output root:

`task/<task_id>/`

Core files:

- `meta.json`
- `results.json`
- `episodes/<idx>/traj.csv`
- `episodes/<idx>/plan.json`
- `episodes/<idx>/images/` (optional)

`traj.csv` schema:

```csv
step,x,y,z
0,....
1,....
```

Coordinates are AirSim world/NED in meters.

---

# 6. Minimal Agent Policy Tips

1. Output exactly one JSON object per step.
2. Use motion JSON (3.1) for normal steps, and done JSON (3.2) only when finished.
3. Keep `turn_angle_deg` incremental (for example 10-30).
4. Keep `forward_distance` conservative (for example 1-5m), then iterate.
5. If `depth_summary.front` is small (near obstacle), turn first, then move.
