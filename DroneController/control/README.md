# control

## Responsibilities
- Own low-level drone motion commands in AirSim.
- Implement translation, rotation, and teleport primitives.
- Expose deterministic motion APIs to upper layers.

## Modules
- drone_motion.py: movement and rotation execution.

## Dependency Direction
- Allowed imports: infra only.
- Should not import: core, io, perception, test.
- core can call control, but control must stay domain-agnostic.
