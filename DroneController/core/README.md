# core

## Responsibilities
- Own online workflow control loop and orchestration.
- Convert sensor observations to prompt payload.
- Parse model output and call motion execution.
- Return run artifacts (trajectory, plan_steps, status).

## Modules
- controller.py: main loop and step lifecycle.
- motion_executor.py: parse/execute bridge and sensor aggregation.
- llm_interface.py: current mock model interaction.

## Dependency Direction
- Allowed imports: control, perception, io, infra, vln_metrics.
- Should not import: test, archive docs, task artifacts.
- Other layers should not depend on core unless they are entry scripts.
