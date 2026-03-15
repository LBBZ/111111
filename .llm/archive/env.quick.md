# Drone Navigation Environment Quick Card

Use this file for first-pass environment understanding.

## Runtime
- Stack: AirSim + EmbodiedCity
- Primary control code: `DroneController/`
- AirSim settings: `others/settings.json`
- Default vehicle: `keli`

## Coordinates and Units
- AirSim uses NED (meters): X forward, Y right, Z down-positive
- `move_up(d)` decreases z; `move_down(d)` increases z
- `start_loc.txt` positions are in centimeters -> convert using `m = cm / 100`
- `label/<idx>.csv` relative trajectory is already in meters

## Dataset (VLN)
- Root: `Datasets/vln/`
- Files: `start_loc.txt`, `label/<idx>.csv`
- Goal computation: `target_pos_m = start_pos_m + rel[-1]`

## Metrics
- `NE = ||final - goal||`
- `SR = 1[NE < success_radius]`, default success radius = 20m
- `SPL = SR * (L / max(L, P))`
  - `L`: GT path length
  - `P`: predicted path length

## Key Entry Points
- Online loop (needs AirSim): `DroneController/test/workflow_test.py`
- Offline smoke eval: `DroneController/run_vln_eval_fake.py`

## Common Pitfalls
1. Do not mix current camera names with legacy VLN camera indexing.
2. Keep vehicle name consistent with settings (`keli`).
3. Use path `Datasets/vln`, not `dataset/vln`.
4. Current `LLMInterface` is mock by default (pipeline validation).
