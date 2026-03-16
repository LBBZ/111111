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
    parser.add_argument("--task_id", type=int, default=0)
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
        "dataset_coord_transform": "x,y,z from cm to m; z uses sign inversion",
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
        # Per-task dataset preprocessing for initialization: cm -> m and z-axis sign inversion.
        start_pos_m_for_init = (
            float(gt.start_pos_raw_cm[0]) / 100.0,
            float(gt.start_pos_raw_cm[1]) / 100.0,
            -float(gt.start_pos_raw_cm[2]) / 100.0,
        )
        init_state = controller.initialize_episode(start_pos_m_for_init, gt.start_rot_deg)
        task_context = {
            "task_id": int(task_id),
            "instruction": gt.instruction,
            "start_rot_deg": list(gt.start_rot_deg),
            "start_yaw_deg": float(gt.start_rot_deg[2]),
            "start_pos_m": list(start_pos_m_for_init),
        }
        meta["episode_init"] = {
            "dataset_index": int(gt.idx),
            "start_pos_raw_cm": list(gt.start_pos_raw_cm),
            "start_pos_m": list(start_pos_m_for_init),
            "start_rot_deg": list(gt.start_rot_deg),
            "start_yaw_deg": float(gt.start_rot_deg[2]),
            "instruction": gt.instruction,
            "applied_state": init_state,
        }
        writer.write_json("meta.json", meta)

        def on_step_end(**kwargs):
            writer.save_step_visual(
                step_idx=int(kwargs["step_count"]),
                sensor_data=kwargs["sensor_data"],
                camera=controller.executor.camera,
            )

        run_artifacts = controller.run(max_steps=200, on_step_end=on_step_end, task_context=task_context)
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
