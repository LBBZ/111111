import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from DroneController.core.controller import DroneController
from DroneController import vln_metrics
from DroneController.io.artifact_writer import WorkflowArtifactWriter


def main() -> int:
    parser = argparse.ArgumentParser(description="Run online single-case VLN workflow evaluation.")
    parser.add_argument("--dataset_root", type=str, default=str(Path("Datasets") / "vln"))
    parser.add_argument("--task_root", type=str, default="task")
    parser.add_argument("--task_id", type=int, required=True)
    args = parser.parse_args()

    task_id = int(args.task_id)
    dataset_root = Path(args.dataset_root)
    output_dir = Path(args.task_root) / str(task_id)
    writer = WorkflowArtifactWriter(output_dir)
    writer.prepare_for_rerun()

    started_at = writer.now_str()
    meta = {
        "task_id": task_id,
        "dataset_root": str(dataset_root),
        "started_at": started_at,
        "finished_at": None,
        "controller_mode": "online_airsim_mock_llm",
        "script": "DroneController/run_vln_workflow_eval.py",
    }
    writer.write_json("meta.json", meta)

    try:
        gt = vln_metrics.load_gt_episode(dataset_root, task_id)
    except Exception as e:
        meta["finished_at"] = writer.now_str()
        meta["error"] = f"Failed to load ground truth episode: {e}"
        writer.write_json("meta.json", meta)
        print(meta["error"])
        return 1

    try:
        controller = DroneController(output_dir=str(output_dir), overwrite_logs=True)

        def on_step_end(**kwargs):
            writer.save_step_visual(
                step_idx=int(kwargs["step_count"]),
                sensor_data=kwargs["sensor_data"],
                camera=controller.executor.camera,
            )

        run_artifacts = controller.run(max_steps=200, on_step_end=on_step_end)
    except Exception as e:
        meta["finished_at"] = writer.now_str()
        meta["error"] = f"Controller run failed (AirSim may be unavailable): {e}"
        writer.write_json("meta.json", meta)
        print(meta["error"])
        return 1

    pred_positions = run_artifacts.get("trajectory", [])
    plan_steps = run_artifacts.get("plan_steps", [])
    status = run_artifacts.get("status", {})

    if len(pred_positions) == 0:
        meta["finished_at"] = writer.now_str()
        meta["error"] = "Controller returned empty trajectory."
        writer.write_json("meta.json", meta)
        print(meta["error"])
        return 1

    metrics = vln_metrics.compute_vln_metrics(gt, pred_positions_m=pred_positions)

    success = int(metrics["SR"])
    results = {
        "task_id": task_id,
        "success": success,
        "ne": float(metrics["NE"]),
        "spl": float(metrics["SPL"]),
        "sr": float(metrics["SR"]),
        "path_length_pred": float(metrics["pred_len_m"]),
        "path_length_gt": float(metrics["gt_len_m"]),
        "steps": int(status.get("step_count", len(plan_steps))),
        "end_reason": str(status.get("end_reason", "unknown")),
    }

    writer.write_traj_csv("traj.csv", pred_positions)
    writer.write_json("plan.json", plan_steps)
    writer.write_json("results.json", results)

    meta["finished_at"] = writer.now_str()
    writer.write_json("meta.json", meta)

    print(
        f"task={task_id} SR={results['sr']:.3f} NE={results['ne']:.3f} SPL={results['spl']:.3f} "
        f"steps={results['steps']} end_reason={results['end_reason']} out={output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
