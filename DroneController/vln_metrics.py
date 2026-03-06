import csv
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import numpy as np


@dataclass(frozen=True)
class EpisodeGT:
    idx: int
    start_pos_m: np.ndarray  # (3,) meters, AirSim world/NED coords
    start_yaw_deg: float
    instruction: str
    target_pos_m: np.ndarray  # (3,) meters
    gt_path_len_m: float


def _parse_start_loc_line(line: str) -> Tuple[int, np.ndarray, float, str]:
    """
    Dataset line example:
      0. 650150.258149, -419969.413753, 131.595741; 旋转: 0, 0, 180; Under the traffic light...

    Assumptions (aligned with `embodied_vln.py`):
    - Position in file is Unreal units (cm); convert to meters by /100.
    - Yaw is in degrees (the 3rd number after '旋转:').
    """
    line = line.strip()
    if not line:
        raise ValueError("Empty start_loc line")

    m = re.match(r"^\s*(\d+)\.\s*([^;]+);\s*旋转:\s*([^;]+);\s*(.*)\s*$", line)
    if not m:
        raise ValueError(f"Unrecognized start_loc format: {line}")

    idx = int(m.group(1))
    pos_part = m.group(2)
    rot_part = m.group(3)
    instruction = m.group(4)

    pos_vals = [p.strip() for p in pos_part.split(",")]
    if len(pos_vals) != 3:
        raise ValueError(f"Expected 3 position values, got {pos_vals}")
    pos_cm = np.array(list(map(float, pos_vals)), dtype=np.float64)
    pos_m = pos_cm / 100.0

    rot_vals = [p.strip() for p in rot_part.split(",")]
    if len(rot_vals) != 3:
        raise ValueError(f"Expected 3 rotation values, got {rot_vals}")
    yaw_deg = float(rot_vals[2])
    return idx, pos_m, yaw_deg, instruction


def load_gt_episode(dataset_root: str | Path, idx: int) -> EpisodeGT:
    dataset_root = Path(dataset_root)
    start_loc_path = dataset_root / "start_loc.txt"
    label_path = dataset_root / "label" / f"{idx}.csv"

    if not start_loc_path.is_file():
        raise FileNotFoundError(f"Missing start_loc.txt: {start_loc_path}")
    if not label_path.is_file():
        raise FileNotFoundError(f"Missing label csv: {label_path}")

    start_lines = start_loc_path.read_text(encoding="utf-8").splitlines()
    if idx < 0 or idx >= len(start_lines):
        raise IndexError(f"idx={idx} out of range for {start_loc_path} ({len(start_lines)} lines)")

    ep_idx, start_pos_m, yaw_deg, instruction = _parse_start_loc_line(start_lines[idx])

    # label/*.csv stores a sequence of relative displacements (meters) from start, one per step:
    # ,x,y,z
    # 0,0,0,....
    # 1,-10,...  (meters)
    rel = _read_label_relative_positions(label_path)
    target_pos_m = start_pos_m + rel[-1]
    gt_len = _path_length(rel)

    return EpisodeGT(
        idx=ep_idx,
        start_pos_m=start_pos_m,
        start_yaw_deg=yaw_deg,
        instruction=instruction,
        target_pos_m=target_pos_m,
        gt_path_len_m=float(gt_len),
    )


def _read_label_relative_positions(csv_path: Path) -> np.ndarray:
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    # skip header row
    if len(rows) < 2:
        raise ValueError(f"Label csv too short: {csv_path}")

    rel = []
    for r in rows[1:]:
        # expected: [step_idx, x, y, z]
        if len(r) < 4:
            continue
        x, y, z = map(float, r[1:4])
        rel.append([x, y, z])

    if len(rel) == 0:
        raise ValueError(f"No trajectory points parsed from {csv_path}")

    return np.asarray(rel, dtype=np.float64)


def _path_length(points: np.ndarray) -> float:
    """Sum of Euclidean distances along a polyline of absolute offsets."""
    points = np.asarray(points, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError(f"Expected (N,3) points, got {points.shape}")
    total = 0.0
    prev = np.zeros(3, dtype=np.float64)
    for p in points:
        total += float(np.linalg.norm(p - prev))
        prev = p
    return total


def trajectory_length_m(positions_m: Iterable[Iterable[float]]) -> float:
    positions = np.asarray(list(positions_m), dtype=np.float64)
    if positions.shape[0] < 2:
        return 0.0
    diffs = positions[1:] - positions[:-1]
    return float(np.sum(np.linalg.norm(diffs, axis=1)))


def final_position_m(positions_m: Iterable[Iterable[float]]) -> np.ndarray:
    positions = np.asarray(list(positions_m), dtype=np.float64)
    if positions.shape[0] == 0:
        raise ValueError("Empty trajectory positions")
    return positions[-1]


def compute_vln_metrics(
    gt: EpisodeGT,
    pred_positions_m: Iterable[Iterable[float]],
    success_radius_m: float = 20.0,
) -> dict:
    """
    Continuous-space SR/NE/SPL (same as patched `embodied_vln.py`):
    - SR_i = 1[dist(final, goal) < success_radius]
    - NE_i = dist(final, goal)
    - SPL_i = SR_i * (L_i / max(L_i, P_i))
      where L_i is GT path length, P_i is predicted path length.
    """
    pred_positions = np.asarray(list(pred_positions_m), dtype=np.float64)
    if pred_positions.ndim != 2 or pred_positions.shape[1] != 3:
        raise ValueError(f"Expected pred positions (N,3), got {pred_positions.shape}")

    final_pos = pred_positions[-1]
    ne = float(np.linalg.norm(final_pos - gt.target_pos_m))
    sr = float(ne < success_radius_m)
    p_len = trajectory_length_m(pred_positions)
    l_len = float(gt.gt_path_len_m)
    denom = max(l_len, p_len) if max(l_len, p_len) > 1e-8 else 1e-8
    spl = sr * (l_len / denom)
    return {
        "idx": gt.idx,
        "SR": sr,
        "NE": ne,
        "SPL": spl,
        "pred_len_m": p_len,
        "gt_len_m": l_len,
        "success_radius_m": float(success_radius_m),
    }


def parse_task_test_positions(task_test_txt: str | Path) -> List[List[float]]:
    """
    Parse `DroneController/task_test/task_test.txt` for a quick sanity-check.
    We use each step's End Position as a trajectory point.
    """
    task_test_txt = Path(task_test_txt)
    text = task_test_txt.read_text(encoding="utf-8")
    # Example line: "  Position: x=-7.45, y=0.00, z=-0.02"
    pos_re = re.compile(r"^\s*Position:\s*x=([-\d.]+),\s*y=([-\d.]+),\s*z=([-\d.]+)\s*$", re.M)

    # Keep only "End Position" blocks by scanning sequentially.
    lines = text.splitlines()
    positions: List[List[float]] = []
    in_end_block = False
    for line in lines:
        if line.strip() == "End Position":
            in_end_block = True
            continue
        if line.strip() == "Start Position":
            in_end_block = False
            continue
        if not in_end_block:
            continue
        m = pos_re.match(line)
        if m:
            positions.append([float(m.group(1)), float(m.group(2)), float(m.group(3))])
            in_end_block = False
    return positions


if __name__ == "__main__":
    # Example usage (sanity check only):
    # - Use a recorded trajectory (here: random motion log) to compute metrics against episode 0 GT.
    #   Real evaluation should feed positions produced by your policy/controller for the same episode.
    dataset_root = Path("Datasets") / "vln"
    gt0 = load_gt_episode(dataset_root, idx=0)
    pred = parse_task_test_positions(Path("DroneController") / "task_test" / "task_test.txt")
    if len(pred) == 0:
        raise SystemExit("No positions parsed from task_test.txt")
    metrics = compute_vln_metrics(gt0, pred_positions_m=pred, success_radius_m=20.0)
    print(metrics)

