import argparse
import sys
from pathlib import Path
from typing import Any, Dict

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from DroneController.core.controller import DroneController
from DroneController import vln_metrics
from DroneController.io.artifact_writer import WorkflowArtifactWriter


def _run_one_task(task_id: int, dataset_root: Path, task_root: Path) -> int:
    print(f"[workflow][task={task_id}] ===== start =====")
    output_dir = task_root / str(task_id)
    writer = WorkflowArtifactWriter(output_dir)
    writer.prepare_for_rerun()

    started_at = writer.now_str()
    meta: Dict[str, Any] = {}
    meta.update(
        {
            "task_id": task_id,
            "dataset_root": str(dataset_root),
            "started_at": started_at,
            "finished_at": None,
            "controller_mode": "online_airsim_mock_llm",
            "script": "DroneController/run_vln_workflow_eval.py",
            "dataset_input_priority": "json(episode_index.json+groups.json) > start_loc.txt",
            "dataset_coord_transform": "use preprocessed start_pos_m from vln_metrics (cm->m, z sign handled there)",
        }
    )
    writer.write_json("meta.json", meta)
    print(f"[workflow][task={task_id}] meta initialized: {output_dir / 'meta.json'}")

    try:
        print(f"[workflow][task={task_id}] load_gt:start")
        gt = vln_metrics.load_gt_episode(dataset_root, task_id)
        print(f"[workflow][task={task_id}] load_gt:ok idx={gt.idx} instruction={gt.instruction}")
    except Exception as e:
        meta["finished_at"] = writer.now_str()
        meta["error"] = f"Failed to load ground truth episode: {e}"
        writer.write_json("meta.json", meta)
        print(meta["error"])
        return 1

    try:
        print(f"[workflow][task={task_id}] controller:init")
        controller = DroneController(output_dir=str(output_dir), overwrite_logs=True)
        # start_pos_m is already normalized by vln_metrics.load_gt_episode.
        start_pos_m_for_init = tuple(map(float, gt.start_pos_m))
        print(f"[workflow][task={task_id}] initialize_episode:start pos={start_pos_m_for_init} rot={gt.start_rot_deg}")
        init_state = controller.initialize_episode(start_pos_m_for_init, gt.start_rot_deg)
        print(f"[workflow][task={task_id}] initialize_episode:ok state={init_state}")
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
        print(f"[workflow][task={task_id}] meta updated with episode_init")

        def on_step_end(**kwargs):
            print(f"[workflow][task={task_id}][step={kwargs.get('step_count')}] save_step_visual:start")
            writer.save_step_visual(
                step_idx=int(kwargs["step_count"]),
                sensor_data=kwargs["sensor_data"],
                camera=controller.executor.camera,
            )
            print(f"[workflow][task={task_id}][step={kwargs.get('step_count')}] save_step_visual:ok")

        print(f"[workflow][task={task_id}] controller.run:start")
        run_artifacts = controller.run(max_steps=200, on_step_end=on_step_end, task_context=task_context)
        print(f"[workflow][task={task_id}] controller.run:ok")
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

    print(f"[workflow][task={task_id}] metrics:start")
    metrics = vln_metrics.compute_vln_metrics(gt, pred_positions_m=pred_positions)
    print(f"[workflow][task={task_id}] metrics:ok SR={metrics['SR']:.3f} NE={metrics['NE']:.3f} SPL={metrics['SPL']:.3f}")

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
    print(f"[workflow][task={task_id}] artifacts written (traj/plan/results)")

    meta["finished_at"] = writer.now_str()
    writer.write_json("meta.json", meta)

    print(
        f"task={task_id} SR={results['sr']:.3f} NE={results['ne']:.3f} SPL={results['spl']:.3f} "
        f"steps={results['steps']} end_reason={results['end_reason']} out={output_dir}"
    )
    print(f"[workflow][task={task_id}] ===== end =====")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run online VLN workflow evaluation (single task or task sequence).")
    parser.add_argument("--dataset_root", type=str, default=str(Path("Datasets") / "vln"))
    parser.add_argument("--task_root", type=str, default="task")
    parser.add_argument("--task_id", type=int, default=None, help="Single task id (kept for compatibility).")
    parser.add_argument("--task_ids", type=int, nargs="+", default=None, help="Task sequence, e.g. --task_ids 1 2 3")
    args = parser.parse_args()

    dataset_root = Path(args.dataset_root)
    task_root = Path(args.task_root)

    if args.task_ids is not None and len(args.task_ids) > 0:
        task_ids = [int(t) for t in args.task_ids]
    elif args.task_id is not None:
        task_ids = [int(args.task_id)]
    else:
        task_ids = [0]

    exit_code = 0
    print(f"[workflow] task sequence={task_ids}")
    for tid in task_ids:
        print(f"[workflow] dispatch task_id={tid}")
        code = _run_one_task(tid, dataset_root=dataset_root, task_root=task_root)
        if code != 0:
            exit_code = 1
            print(f"[workflow] task_id={tid} failed")
        else:
            print(f"[workflow] task_id={tid} success")
    print(f"[workflow] all done exit_code={exit_code}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
