# Drone Navigation Agent API

This file defines the **observation interface, action interface, and output protocol** used by the navigation agent.

---

# Observation Interface

Observations are produced by:

```
DroneController/DroneCamera
```

The drone provides **9 camera views**:

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

Each direction provides:

```
RGB image
Depth image
Depth NPY (float32 meters)
```

These views represent the local environment around the drone.

---

# Action Interface

Actions are implemented in:

```
DroneController/drone_motion.py
```

---

## Translation (meters)

```
move_forward(d)
move_backward(d)

move_left(d)
move_right(d)

move_up(d)
move_down(d)
```

---

## Rotation (degrees)

```
turn_left(angle_deg)
turn_right(angle_deg)
```

---

# Action Constraints

Each step must output **one action only**.

Recommended ranges:

```
translation : 5–10 meters
rotation    : 10–45 degrees
```

---

# Navigation Loop

Each planning step receives:

```
current drone pose
9 camera observations
task instruction
(optional) trajectory history
```

The agent must:

```
analyze environment
estimate navigable direction
move toward the goal
output the next action
```

Planning happens **one step at a time**.

---

# Output Format

Each step must return a JSON object.

Example:

```json
{
  "action": "move_forward",
  "value": 8.0,
  "reason": "front path is clear and moves toward the goal"
}
```

Stop action:

```json
{
  "action": "stop",
  "reason": "drone is close enough to the target region"
}
```

Rules:

```
one action per step
valid action name only
```
