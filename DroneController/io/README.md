# io

## Responsibilities
- Own task artifact writing and logging outputs.
- Manage run output lifecycle and overwrite behavior.
- Keep file schemas stable for automation.

## Modules
- logger.py: text + machine-readable run logs.
- artifact_writer.py: task output writer and cleanup helper.

## Dependency Direction
- Must not import core/control/perception.
- Can import stdlib and light utility modules only.
- core and entry scripts call io, not the reverse.
