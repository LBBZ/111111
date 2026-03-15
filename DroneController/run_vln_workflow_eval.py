import argparse
import csv
import json
import shutil
import sys
import time
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from DroneController.controller import DroneController
from DroneController import vln_metrics


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _write_traj_csv(path: Path, positions_m) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["step", "x", "y", "z"])
        for i, p in enumerate(positions_m):
            x, y, z = map(float, p)
            writer.writerow([i, x, y, z])


def _now_str() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def main() -> int:
    parser = argparse.ArgumentParser(description="Run online single-case VLN workflow evaluation.")
    parser.add_argument("--dataset_root", type=str, default=str(Path("Datasets") / "vln"))
    parser.add_argument("--task_root", type=str, default="task")
    parser.add_argument("--task_id", type=int, required=True)
    args = parser.parse_args()

    task_id = int(args.task_id)
    dataset_root = Path(args.dataset_root)
    output_dir = Path(args.task_root) / str(task_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Remove legacy offline nested directory to keep flat output layout.
    old_episodes_dir = output_dir / "episodes"
    if old_episodes_dir.exists() and old_episodes_dir.is_dir():
        shutil.rmtree(old_episodes_dir)

    started_at = _now_str()
    meta = {
        "task_id": task_id,
        "dataset_root": str(dataset_root),
        "started_at": started_at,
        "finished_at": None,
        "controller_mode": "online_airsim_mock_llm",
        "script": "DroneController/run_vln_workflow_eval.py",
    }
    _write_json(output_dir / "meta.json", meta)

    try:
        gt = vln_metrics.load_gt_episode(dataset_root, task_id)
    except Exception as e:
        meta["finished_at"] = _now_str()
        meta["error"] = f"Failed to load ground truth episode: {e}"
        _write_json(output_dir / "meta.json", meta)
        print(meta["error"])
        return 1

    try:
        controller = DroneController(output_dir=str(output_dir), overwrite_logs=True)
        run_artifacts = controller.run(max_steps=200)
    except Exception as e:
        meta["finished_at"] = _now_str()
        meta["error"] = f"Controller run failed (AirSim may be unavailable): {e}"
        _write_json(output_dir / "meta.json", meta)
        print(meta["error"])
        return 1

    pred_positions = run_artifacts.get("trajectory", [])
    plan_steps = run_artifacts.get("plan_steps", [])
    status = run_artifacts.get("status", {})

    if len(pred_positions) == 0:
        meta["finished_at"] = _now_str()
        meta["error"] = "Controller returned empty trajectory."
        _write_json(output_dir / "meta.json", meta)
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

    _write_traj_csv(output_dir / "traj.csv", pred_positions)
    _write_json(output_dir / "plan.json", plan_steps)
    _write_json(output_dir / "results.json", results)

    meta["finished_at"] = _now_str()
    _write_json(output_dir / "meta.json", meta)

    print(
        f"task={task_id} SR={results['sr']:.3f} NE={results['ne']:.3f} SPL={results['spl']:.3f} "
        f"steps={results['steps']} end_reason={results['end_reason']} out={output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
