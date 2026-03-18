import json
from pathlib import Path
from typing import Iterable, List

from DroneController.io.workflow_logger import WorkflowLogger
from DroneController.workflow.models import TaskRunResult, TaskSpec, WorkflowRunResult
from DroneController.workflow.task_processor import TaskProcessor


class WorkflowManager:
    """Workflow entry: bootstrap first, then run task sequence one by one."""

    def __init__(self, dataset_root: Path, task_root: Path, max_steps: int = 200, bootstrap_max_steps: int = 5):
        self.dataset_root = Path(dataset_root)
        self.task_root = Path(task_root)
        self.logger = WorkflowLogger(self.task_root)
        self.processor = TaskProcessor(
            dataset_root=self.dataset_root,
            task_root=self.task_root,
            script_name="DroneController/run_vln_workflow_eval.py",
            max_steps=max_steps,
            bootstrap_max_steps=bootstrap_max_steps,
        )

    @staticmethod
    def _normalize_task_ids(task_ids: Iterable[int]) -> List[int]:
        out = [int(t) for t in task_ids]
        if not out:
            raise ValueError("task_ids is empty")
        return out

    def _write_summary_json(self, bootstrap_result: TaskRunResult, task_results: List[TaskRunResult]) -> None:
        summary = {
            "dataset_root": str(self.dataset_root),
            "task_root": str(self.task_root),
            "bootstrap": {
                "task_id": bootstrap_result.task_id,
                "ok": bootstrap_result.ok,
                "end_reason": bootstrap_result.end_reason,
                "error": bootstrap_result.error,
                "output_dir": bootstrap_result.output_dir,
            },
            "tasks": [
                {
                    "task_id": r.task_id,
                    "task_kind": r.task_kind,
                    "ok": r.ok,
                    "end_reason": r.end_reason,
                    "steps": r.steps,
                    "error": r.error,
                    "metrics": r.metrics,
                    "output_dir": r.output_dir,
                }
                for r in task_results
            ],
            "all_ok": bootstrap_result.ok and all(r.ok for r in task_results),
        }
        path = self.task_root / "workflow_summary.json"
        path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    def run(self, task_ids: Iterable[int]) -> WorkflowRunResult:
        normalized_ids = self._normalize_task_ids(task_ids)
        self.logger.info(f"workflow start dataset_root={self.dataset_root} task_ids={normalized_ids}")

        bootstrap_spec = TaskSpec(task_id="bootstrap", task_kind="bootstrap_simple", source_task_id=normalized_ids[0])
        self.logger.task_start(bootstrap_spec.task_id, bootstrap_spec.task_kind)
        try:
            bootstrap_result = self.processor.run_one(bootstrap_spec)
        except Exception as exc:  # pragma: no cover - processor already handles expected failures
            bootstrap_result = TaskRunResult(
                task_id=bootstrap_spec.task_id,
                task_kind=bootstrap_spec.task_kind,
                output_dir=str(self.task_root / "bootstrap"),
                ok=False,
                end_reason="error",
                steps=0,
                error=str(exc),
            )
        self.logger.task_end(
            bootstrap_spec.task_id,
            ok=bootstrap_result.ok,
            end_reason=bootstrap_result.end_reason,
        )
        if not bootstrap_result.ok:
            self.logger.warn("bootstrap failed, continue dispatching normal tasks")

        task_results: List[TaskRunResult] = []
        for task_id in normalized_ids:
            spec = TaskSpec(task_id=task_id, task_kind="vln")
            self.logger.task_start(spec.task_id, spec.task_kind)
            try:
                result = self.processor.run_one(spec)
            except Exception as exc:  # pragma: no cover - processor already handles expected failures
                result = TaskRunResult(
                    task_id=spec.task_id,
                    task_kind=spec.task_kind,
                    output_dir=str(self.task_root / str(spec.task_id)),
                    ok=False,
                    end_reason="error",
                    steps=0,
                    error=str(exc),
                )
            task_results.append(result)
            self.logger.task_end(
                spec.task_id,
                ok=result.ok,
                end_reason=result.end_reason,
            )
            if not result.ok:
                self.logger.warn(f"task_id={spec.task_id} failed, continue to next task")

        self._write_summary_json(bootstrap_result=bootstrap_result, task_results=task_results)
        ok_count = len([r for r in task_results if r.ok])
        self.logger.info(
            f"workflow summary bootstrap_ok={bootstrap_result.ok} "
            f"task_total={len(task_results)} task_ok={ok_count} task_failed={len(task_results) - ok_count}"
        )
        self.logger.info("workflow end")
        return WorkflowRunResult(bootstrap_ok=bootstrap_result.ok, task_results=task_results)


