# Project Structure for Development Agent

Scope: practical architecture map for coding tasks.

## Active Runtime Tree (DroneController)
- core/
  - controller.py
  - motion_executor.py
  - llm_interface.py
- control/
  - drone_motion.py
- perception/
  - drone_camera.py
  - image_processing.py
- infra/
  - airsim_client.py
- io/
  - logger.py
  - artifact_writer.py
- workflow/
  - models.py
  - task_processor.py
  - manager.py
- run_vln_workflow_eval.py
- run_vln_eval_fake.py
- vln_metrics.py

## Responsibility Boundaries
- core: orchestration and business flow.
- control: movement primitives only.
- perception: sensor capture/processing only.
- infra: infrastructure clients only.
- io: write/read artifacts and logs only.

## Common Extension Points
- Add new workflow script at DroneController/ root only if it is an entry point.
- Add reusable logic into the correct layer package.
- Keep task output schema stable unless explicitly changed.

## Related Paths Outside DroneController
- Dataset: Datasets/vln
- Task output: task/<task_id>/
- Reference stack (non-primary): vln/, prompts/, embodied_vln.py
