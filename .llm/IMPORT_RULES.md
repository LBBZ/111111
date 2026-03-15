# Import Rules for Development Agent

Authoritative source: .llm/AGENT_TOTAL_RULE.md

## Layer Import Matrix
- core -> control/perception/io/infra
- control -> infra
- perception -> infra
- io -> stdlib/local only
- infra -> external libs only

## Deprecated Flat Imports (Do Not Use)
- DroneController.controller
- DroneController.motion_executor
- DroneController.llm_interface
- DroneController.drone_motion
- DroneController.drone_camera
- DroneController.image_processing
- DroneController.airsim_client
- DroneController.logger
- DroneController.artifact_writer

## Use Layered Imports Instead
- DroneController.core.controller
- DroneController.core.motion_executor
- DroneController.core.llm_interface
- DroneController.control.drone_motion
- DroneController.perception.drone_camera
- DroneController.perception.image_processing
- DroneController.infra.airsim_client
- DroneController.io.logger
- DroneController.io.artifact_writer
