import argparse
import csv
import json
import time
from pathlib import Path
from typing import Iterable, List

# Legacy offline utility for fake/batch evaluation.
# Online single-case workflow entry: DroneController/run_vln_workflow_eval.py

import random

import numpy as np

import vln_metrics


def _now_task_id() -> str:
    return time.strftime("%Y%m%d_%H%M%S", time.localtime())


def _write_traj_csv(path: Path, positions_m: Iterable[Iterable[float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["step", "x", "y", "z"])
        for i, p in enumerate(positions_m):
            x, y, z = map(float, p)
            w.writerow([i, x, y, z])


def _write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_rel(dataset_root: Path, idx: int) -> np.ndarray:
    label_path = dataset_root / "label" / f"{idx}.csv"
    return vln_metrics._read_label_relative_positions(label_path)  # noqa: SLF001


def _fake_pred_positions(
    gt: vln_metrics.EpisodeGT,
    rel,
    variant: str,
    rng: random.Random,
    success_radius_m: float,
) -> List[List[float]]:
    """
    Return predicted absolute positions (meters) in world/NED coords.
    Variants:
      - hi: follow GT closely (SR=1, SPL≈1)
      - mid: detour + still end within success radius (SR=1, SPL<1)
      - fail: end outside success radius (SR=0, SPL=0)
    """
    abs_gt: List[List[float]] = []
    sx, sy, sz = gt.start_pos_m
    for (rx, ry, rz) in rel:
        abs_gt.append([sx + float(rx), sy + float(ry), sz + float(rz)])

    if variant == "hi":
        out = []
        for x, y, z in abs_gt:
            out.append([x + rng.gauss(0.0, 0.5), y + rng.gauss(0.0, 0.5), z + rng.gauss(0.0, 0.5)])
        return out

    if variant == "mid":
        n = len(abs_gt)
        mid_idx = max(1, n // 2)
        prefix = abs_gt[:mid_idx]

        tx, ty, tz = gt.target_pos_m
        detour = [tx, ty + float(min(15.0, success_radius_m * 0.6)), tz]
        end = [tx + rng.gauss(0.0, 2.0), ty + rng.gauss(0.0, 2.0), tz + rng.gauss(0.0, 2.0)]

        def lerp(a, b, k: int):
            out = []
            if k <= 1:
                return [b]
            for i in range(k):
                t = i / (k - 1)
                out.append(
                    [
                        a[0] * (1 - t) + b[0] * t,
                        a[1] * (1 - t) + b[1] * t,
                        a[2] * (1 - t) + b[2] * t,
                    ]
                )
            return out

        seg1 = lerp(prefix[-1], detour, k=10)
        seg2 = lerp(detour, end, k=10)
        return prefix + seg1[1:] + seg2[1:]

    if variant == "fail":
        n = len(abs_gt)
        take = min(max(2, n // 3), n)
        prefix = abs_gt[:take]
        tx, ty, tz = gt.target_pos_m
        end = [tx + float(success_radius_m + 10.0), ty, tz]
        return prefix + [end]

    raise ValueError(f"Unknown variant: {variant}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate fake VLN trajectories and compute SR/NE/SPL.")
    parser.add_argument("--dataset_root", type=str, default=str(Path("Datasets") / "vln"))
    parser.add_argument("--out_root", type=str, default="task")
    parser.add_argument("--task_id", type=str, default=_now_task_id())
    parser.add_argument("--episodes", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--success_radius", type=float, default=20.0)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    dataset_root = Path(args.dataset_root)
    out_root = Path(args.out_root)
    task_id = args.task_id
    success_radius_m = float(args.success_radius)

    task_dir = out_root / task_id
    episodes_dir = task_dir / "episodes"

    meta = {
        "task_id": task_id,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "dataset_root": str(dataset_root),
        "episodes": list(map(int, args.episodes)),
        "success_radius_m": success_radius_m,
        "note": "Fake trajectories for evaluation pipeline smoke test (no AirSim, no LLM).",
        "artifacts": {
            "per_episode": ["plan.json", "traj.csv", "images/"],
            "root": ["meta.json", "results.json"],
        },
    }
    _write_json(task_dir / "meta.json", meta)

    per_ep_results: List[dict] = []
    variants = ["hi", "mid", "fail"]

    for i, ep_idx in enumerate(args.episodes):
        variant = variants[i % len(variants)]

        gt = vln_metrics.load_gt_episode(dataset_root, idx=int(ep_idx))
        rel = _load_rel(dataset_root, idx=int(ep_idx))

        rng = random.Random(args.seed + int(ep_idx) * 100 + i)
        pred = _fake_pred_positions(gt, rel, variant=variant, rng=rng, success_radius_m=success_radius_m)

        ep_out = episodes_dir / str(ep_idx)
        (ep_out / "images").mkdir(parents=True, exist_ok=True)

        _write_traj_csv(ep_out / "traj.csv", pred)
        plan = {
            "episode_idx": int(ep_idx),
            "variant": variant,
            "instruction": gt.instruction,
            "policy": {"type": "fake", "description": "Deterministic fake policy for pipeline validation."},
            "steps": [
                {
                    "step": int(k),
                    "action": None,
                    "reason": "fake_pred_positions: position-only trajectory (no actions yet)",
                }
                for k in range(int(len(pred)))
            ],
        }
        _write_json(ep_out / "plan.json", plan)

        metrics = vln_metrics.compute_vln_metrics(gt, pred_positions_m=pred, success_radius_m=success_radius_m)
        per_ep_results.append(
            {
                "episode": {"idx": int(ep_idx), "instruction": gt.instruction, "start_yaw_deg": gt.start_yaw_deg},
                "gt": {
                    "start_pos_m": list(gt.start_pos_m),
                    "target_pos_m": list(gt.target_pos_m),
                    "gt_path_len_m": float(gt.gt_path_len_m),
                },
                "pred": {
                    "traj_csv": str((ep_out / "traj.csv").as_posix()),
                    "num_points": int(len(pred)),
                },
                "metrics": metrics,
                "variant": variant,
            }
        )

    sr_vals = [r["metrics"]["SR"] for r in per_ep_results]
    ne_vals = [r["metrics"]["NE"] for r in per_ep_results]
    spl_vals = [r["metrics"]["SPL"] for r in per_ep_results]
    def mean(xs: List[float]) -> float:
        return sum(xs) / len(xs) if xs else 0.0

    summary = {"num_episodes": len(per_ep_results), "SR_mean": mean(sr_vals), "NE_mean": mean(ne_vals), "SPL_mean": mean(spl_vals)}

    results = {"meta": meta, "episodes": per_ep_results, "summary": summary}
    _write_json(task_dir / "results.json", results)

    print(f"wrote: {task_dir / 'results.json'}")
    for r in per_ep_results:
        m = r["metrics"]
        print(
            f'ep={r["episode"]["idx"]} variant={r["variant"]} '
            f'SR={m["SR"]:.0f} NE={m["NE"]:.2f} SPL={m["SPL"]:.3f} '
            f'pred_len={m["pred_len_m"]:.2f} gt_len={m["gt_len_m"]:.2f}'
        )
    print(
        f'SUMMARY SR_mean={summary["SR_mean"]:.3f} NE_mean={summary["NE_mean"]:.2f} SPL_mean={summary["SPL_mean"]:.3f}'
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

