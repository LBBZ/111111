from pathlib import Path
from typing import Any, Dict

from DroneController import vln_metrics
from DroneController.core.controller import DroneController
from DroneController.io.artifact_writer import WorkflowArtifactWriter
from DroneController.workflow.models import TaskRunResult, TaskSpec


class TaskProcessor:
    """Run one bootstrap or VLN task with the same lifecycle."""

    def __init__(
        self,
        dataset_root: Path,
        task_root: Path,
        script_name: str,
        max_steps: int = 200,
        bootstrap_max_steps: int = 5,
    ):
        self.dataset_root = Path(dataset_root)
        self.task_root = Path(task_root)
        self.script_name = script_name
        self.max_steps = int(max_steps)
        self.bootstrap_max_steps = int(bootstrap_max_steps)

    def _output_dir_for(self, spec: TaskSpec) -> Path:
        if spec.task_kind == "bootstrap_simple":
            return self.task_root / "bootstrap"
        return self.task_root / str(spec.task_id)

    def _build_meta(self, spec: TaskSpec, writer: WorkflowArtifactWriter) -> Dict[str, Any]:
        meta: Dict[str, Any] = {
            "task_id": spec.task_id,
            "task_kind": spec.task_kind,
            "dataset_root": str(self.dataset_root),
            "started_at": writer.now_str(),
            "finished_at": None,
            "script": self.script_name,
            "source_task_id": spec.source_task_id,
        }
        if spec.task_kind != "bootstrap_simple":
            meta["controller_mode"] = "online_airsim_mock_llm"
            meta["dataset_input_priority"] = "json(episode_index.json+groups.json) > start_loc.txt"
            meta["dataset_coord_transform"] = "use preprocessed start_pos_m from vln_metrics (cm->m, z sign handled there)"
        return meta

    def _append_lifecycle_event(self, writer: WorkflowArtifactWriter, event: Dict[str, Any]) -> None:
        writer.append_jsonl("lifecycle.jsonl", event)

    def run_one(self, spec: TaskSpec) -> TaskRunResult:
        output_dir = self._output_dir_for(spec)
        writer = WorkflowArtifactWriter(output_dir)
        writer.prepare_for_rerun()
        meta = self._build_meta(spec, writer)
        writer.write_json("meta.json", meta)

        try:
            load_idx = int(spec.source_task_id if spec.task_kind == "bootstrap_simple" else spec.task_id)
            self._append_lifecycle_event(writer, {"stage": "load_gt:start", "idx": load_idx, "time": writer.now_str()})
            gt = vln_metrics.load_gt_episode(self.dataset_root, load_idx)
            self._append_lifecycle_event(
                writer,
                {
                    "stage": "load_gt:ok",
                    "idx": int(gt.idx),
                    "instruction": gt.instruction,
                    "time": writer.now_str(),
                },
            )

            controller = DroneController(output_dir=str(output_dir), overwrite_logs=True)
            start_pos_m = tuple(map(float, gt.start_pos_m))
            init_state = controller.initialize_episode(start_pos_m, gt.start_rot_deg)
            meta["episode_init"] = {
                "dataset_index": int(gt.idx),
                "start_pos_raw_cm": list(gt.start_pos_raw_cm),
                "start_pos_m": list(start_pos_m),
                "start_rot_deg": list(gt.start_rot_deg),
                "start_yaw_deg": float(gt.start_rot_deg[2]),
                "instruction": gt.instruction,
                "applied_state": init_state,
            }
            writer.write_json("meta.json", meta)
            self._append_lifecycle_event(writer, {"stage": "initialize:ok", "time": writer.now_str()})

            task_context: Dict[str, Any]
            max_steps = self.max_steps
            if spec.task_kind == "bootstrap_simple":
                task_context = {
                    "task_id": "bootstrap",
                    "task_kind": "bootstrap_simple",
                    "instruction": "Simple warm-up: move up once from initial position.",
                    "start_pos_m": list(start_pos_m),
                    "start_rot_deg": list(gt.start_rot_deg),
                }
                max_steps = self.bootstrap_max_steps
            else:
                task_context = {
                    "task_id": int(spec.task_id),
                    "task_kind": "vln",
                    "instruction": gt.instruction,
                    "start_rot_deg": list(gt.start_rot_deg),
                    "start_yaw_deg": float(gt.start_rot_deg[2]),
                    "start_pos_m": list(start_pos_m),
                }

            def on_step_end(**kwargs):
                step_count = int(kwargs["step_count"])
                stage = str(kwargs.get("stage", "pre_llm"))
                writer.save_step_visual_async(
                    step_idx=step_count,
                    sensor_data=kwargs["sensor_data"],
                    camera=controller.executor.camera,
                )
                self._append_lifecycle_event(
                    writer,
                    {
                        "stage": "step:snapshot_saved",
                        "phase": stage,
                        "step": step_count,
                        "time": writer.now_str(),
                    },
                )

            self._append_lifecycle_event(writer, {"stage": "run:start", "max_steps": int(max_steps), "time": writer.now_str()})
            run_artifacts = controller.run(max_steps=max_steps, on_step_end=on_step_end, task_context=task_context)
            writer.wait_for_pending()
            self._append_lifecycle_event(writer, {"stage": "run:ok", "time": writer.now_str()})

            pred_positions = run_artifacts.get("trajectory", [])
            plan_steps = run_artifacts.get("plan_steps", [])
            status = run_artifacts.get("status", {})

            if not pred_positions:
                raise ValueError("Controller returned empty trajectory")

            writer.write_traj_csv("traj.csv", pred_positions)
            writer.write_json("plan.json", plan_steps)

            if spec.task_kind == "bootstrap_simple":
                metrics: Dict[str, Any] = {
                    "source_task_id": int(load_idx),
                    "steps": int(status.get("step_count", len(plan_steps))),
                    "end_reason": str(status.get("end_reason", "unknown")),
                    "done": bool(status.get("done", False)),
                }
            else:
                m = vln_metrics.compute_vln_metrics(gt, pred_positions_m=pred_positions)
                metrics = {
                    "task_id": int(spec.task_id),
                    "success": int(m["SR"]),
                    "ne": float(m["NE"]),
                    "spl": float(m["SPL"]),
                    "sr": float(m["SR"]),
                    "path_length_pred": float(m["pred_len_m"]),
                    "path_length_gt": float(m["gt_len_m"]),
                    "steps": int(status.get("step_count", len(plan_steps))),
                    "end_reason": str(status.get("end_reason", "unknown")),
                }

            writer.write_json("results.json", metrics)

            meta["finished_at"] = writer.now_str()
            writer.write_json("meta.json", meta)
            return TaskRunResult(
                task_id=spec.task_id,
                task_kind=spec.task_kind,
                output_dir=str(output_dir),
                ok=True,
                end_reason=str(metrics.get("end_reason", "unknown")),
                steps=int(metrics.get("steps", 0)),
                metrics=metrics,
            )
        except Exception as exc:
            meta["finished_at"] = writer.now_str()
            meta["error"] = str(exc)
            writer.write_json("meta.json", meta)
            return TaskRunResult(
                task_id=spec.task_id,
                task_kind=spec.task_kind,
                output_dir=str(output_dir),
                ok=False,
                end_reason="error",
                steps=0,
                error=str(exc),
            )
        finally:
            try:
                writer.close()
            except Exception:
                # Keep task processor side-effect free for workflow logging.
                pass

    @staticmethod
    def describe_saved_files(spec: TaskSpec) -> Dict[str, str]:
        files = {
            "meta.json": "任务元信息（初始化姿态、时间戳、错误信息）",
            "plan.json": "每步决策与动作明细",
            "traj.csv": "轨迹点（step,x,y,z）",
            "results.json": "任务结果指标与终止原因",
            "lifecycle.jsonl": "生命周期阶段日志（可用于问题排查）",
            "drone_log.txt": "控制器详细文本日志",
            "drone_log.json": "控制器结构化日志",
            "step_visual/": "每步图像与深度图快照",
        }
        if spec.task_kind == "bootstrap_simple":
            files["results.json"] = "bootstrap 结果（steps/end_reason/done）"
        return files



