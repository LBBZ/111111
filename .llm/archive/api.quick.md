# Drone Navigation API Quick Card

Use this file for first-pass agent context only.

## Pipeline
1. `MotionExecutor.get_sensor_data()`
2. `MotionExecutor.build_prompt()`
3. `LLMInterface.get_action(prompt)`
4. `MotionExecutor.parse(action_json)`
5. `MotionExecutor.execute(parsed_action)`
6. `Logger.log(...)`

Entry: `DroneController/controller.py` -> `DroneController.run()`

## Observations
- Cameras (9): Front, Back, Left, Right, FrontLeft, FrontRight, BackLeft, BackRight, TopDown
- RGB: `capture_all()`
- Depth (meters, float32): `capture_all_depth()`
- Segmentation: `capture_all_seg()` (currently 5 views)
- Drone state fields: x, y, z, pitch, roll, yaw

## Accepted Action JSON
```json
{
  "turn_direction": "left|right|none",
  "turn_angle_deg": 10.0,
  "forward_distance": 2.0,
  "vertical_movement": 0.0
}
```

Done JSON:
```json
{"done": true, "message": "Mission completed."}
```

## Execution Semantics
- Fixed order: rotate -> forward -> vertical
- `vertical_movement > 0` means move up
- Output exactly one JSON object per step

## Artifacts
- Root: `task/<task_id>/`
- Per episode: `episodes/<idx>/traj.csv`, `episodes/<idx>/plan.json`, optional `images/`
- Summary: `meta.json`, `results.json`
