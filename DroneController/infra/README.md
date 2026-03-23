# infra

## Responsibilities
- Own infrastructure clients and integration plumbing.
- Provide shared singleton connection to AirSim runtime.

## Modules
- airsim_client.py: thread-safe AirSim client singleton.

## Dependency Direction
- Must not import higher layers: core/control/perception/io.
- Can be imported by all runtime layers.
- Keep infra minimal and side-effect aware.
