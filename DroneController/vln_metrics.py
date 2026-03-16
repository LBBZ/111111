import csv
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple, Union

import math


@dataclass(frozen=True)
class EpisodeGT:
    idx: int
    start_pos_m: Tuple[float, float, float]  # (3,) meters, AirSim world/NED coords
    start_rot_deg: Tuple[float, float, float]
    start_yaw_deg: float
    instruction: str
    target_pos_m: Tuple[float, float, float]  # (3,) meters
    gt_path_len_m: float
    start_pos_raw_cm: Tuple[float, float, float]


def _cm_to_start_pos_m(pos_cm: Tuple[float, float, float]) -> Tuple[float, float, float]:
    return (
        float(pos_cm[0]) / 100.0,
        float(pos_cm[1]) / 100.0,
        -float(pos_cm[2]) / 100.0,
    )


def _parse_start_loc_line(
    line: str,
) -> Tuple[int, Tuple[float, float, float], Tuple[float, float, float], str, Tuple[float, float, float]]:
    """
    Dataset line example:
      0. 650150.258149, -419969.413753, 131.595741; 旋转: 0, 0, 180; Under the traffic light...

    Assumptions (aligned with workflow init):
    - Position in file is Unreal units (cm); convert to meters by /100.
    - Dataset z axis is opposite to AirSim NED z; use z_m = -(z_cm / 100).
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
    pos_cm = (float(pos_vals[0]), float(pos_vals[1]), float(pos_vals[2]))
    pos_m = _cm_to_start_pos_m(pos_cm)

    rot_vals = [p.strip() for p in rot_part.split(",")]
    if len(rot_vals) != 3:
        raise ValueError(f"Expected 3 rotation values, got {rot_vals}")
    rot_deg = (float(rot_vals[0]), float(rot_vals[1]), float(rot_vals[2]))
    return idx, pos_m, rot_deg, str(instruction), pos_cm


def _load_episode_from_json(dataset_root: Path, idx: int) -> Dict[str, Any]:
    idx_path = dataset_root / "episode_index.json"
    groups_path = dataset_root / "groups.json"
    if not idx_path.is_file() or not groups_path.is_file():
        raise FileNotFoundError("JSON dataset files not found")

    idx_obj = json.loads(idx_path.read_text(encoding="utf-8"))
    episodes = idx_obj.get("episodes", {})
    ep_ref = episodes.get(str(idx))
    if ep_ref is None:
        raise IndexError(f"idx={idx} not found in {idx_path}")

    group_id = int(ep_ref["group_id"])
    target_key = str(ep_ref["target_key"])

    groups_obj = json.loads(groups_path.read_text(encoding="utf-8"))
    groups = groups_obj.get("groups", [])
    group = next((g for g in groups if int(g.get("group_id", -1)) == group_id), None)
    if group is None:
        raise KeyError(f"group_id={group_id} not found in {groups_path}")

    init = group.get("init", {})
    targets = group.get("targets", {})
    instruction = targets.get(target_key)
    if instruction is None:
        raise KeyError(f"target_key={target_key} missing in group_id={group_id}")

    pos_cm_arr = init.get("pos_cm", [])
    rot_deg_arr = init.get("rot_deg", [])
    if len(pos_cm_arr) != 3 or len(rot_deg_arr) != 3:
        raise ValueError(f"Invalid init pose in group_id={group_id}")

    pos_cm = (float(pos_cm_arr[0]), float(pos_cm_arr[1]), float(pos_cm_arr[2]))
    rot_deg = (float(rot_deg_arr[0]), float(rot_deg_arr[1]), float(rot_deg_arr[2]))
    return {
        "ep_idx": idx,
        "start_pos_raw_cm": pos_cm,
        "start_pos_m": _cm_to_start_pos_m(pos_cm),
        "rot_deg": rot_deg,
        "instruction": str(instruction),
        "label_path": dataset_root / "label" / f"{idx}.csv",
        "source": "json",
    }


def _load_episode_from_start_loc(dataset_root: Path, idx: int) -> Dict[str, Any]:
    start_loc_path = dataset_root / "start_loc.txt"
    if not start_loc_path.is_file():
        raise FileNotFoundError(f"Missing start_loc.txt: {start_loc_path}")

    start_lines = start_loc_path.read_text(encoding="utf-8").splitlines()
    if idx < 0 or idx >= len(start_lines):
        raise IndexError(f"idx={idx} out of range for {start_loc_path} ({len(start_lines)} lines)")

    ep_idx, start_pos_m, rot_deg, instruction, start_pos_raw_cm = _parse_start_loc_line(start_lines[idx])
    return {
        "ep_idx": ep_idx,
        "start_pos_raw_cm": start_pos_raw_cm,
        "start_pos_m": start_pos_m,
        "rot_deg": rot_deg,
        "instruction": instruction,
        "label_path": dataset_root / "label" / f"{idx}.csv",
        "source": "start_loc",
    }


def load_gt_episode(dataset_root: Union[str, Path], idx: int) -> EpisodeGT:
    dataset_root = Path(dataset_root)
    try:
        ep = _load_episode_from_json(dataset_root, idx)
    except Exception:
        ep = _load_episode_from_start_loc(dataset_root, idx)

    ep_idx = int(ep["ep_idx"])
    start_pos_m = ep["start_pos_m"]
    rot_deg = ep["rot_deg"]
    instruction = ep["instruction"]
    start_pos_raw_cm = ep["start_pos_raw_cm"]
    label_path = Path(ep["label_path"])

    if not label_path.is_file():
        raise FileNotFoundError(f"Missing label csv: {label_path}")

    # label/*.csv stores a sequence of relative displacements (meters) from start, one per step:
    # ,x,y,z
    # 0,0,0,....
    # 1,-10,...  (meters)
    rel = _read_label_relative_positions(label_path)
    last = rel[-1]
    target_pos_m = (start_pos_m[0] + last[0], start_pos_m[1] + last[1], start_pos_m[2] + last[2])
    gt_len = _path_length(rel)

    return EpisodeGT(
        idx=ep_idx,
        start_pos_m=start_pos_m,
        start_rot_deg=rot_deg,
        start_yaw_deg=float(rot_deg[2]),
        instruction=instruction,
        target_pos_m=target_pos_m,
        gt_path_len_m=float(gt_len),
        start_pos_raw_cm=start_pos_raw_cm,
    )


def _read_label_relative_positions(csv_path: Path) -> List[Tuple[float, float, float]]:
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if len(rows) < 2:
        raise ValueError(f"Label csv too short: {csv_path}")

    rel: List[Tuple[float, float, float]] = []
    for r in rows[1:]:
        # expected: [step_idx, x, y, z]
        if len(r) < 4:
            continue
        x, y, z = map(float, r[1:4])
        rel.append((x, y, z))

    if len(rel) == 0:
        raise ValueError(f"No trajectory points parsed from {csv_path}")

    return rel


def _path_length(points: Iterable[Tuple[float, float, float]]) -> float:
    """Sum of Euclidean distances along a polyline of absolute offsets."""
    total = 0.0
    px, py, pz = 0.0, 0.0, 0.0
    for x, y, z in points:
        dx, dy, dz = x - px, y - py, z - pz
        total += math.sqrt(dx * dx + dy * dy + dz * dz)
        px, py, pz = x, y, z
    return total


def trajectory_length_m(positions_m: Iterable[Iterable[float]]) -> float:
    pts = [tuple(map(float, p)) for p in positions_m]
    if len(pts) < 2:
        return 0.0
    total = 0.0
    (px, py, pz) = pts[0]
    for (x, y, z) in pts[1:]:
        dx, dy, dz = x - px, y - py, z - pz
        total += math.sqrt(dx * dx + dy * dy + dz * dz)
        px, py, pz = x, y, z
    return total


def final_position_m(positions_m: Iterable[Iterable[float]]) -> Tuple[float, float, float]:
    pts = [tuple(map(float, p)) for p in positions_m]
    if len(pts) == 0:
        raise ValueError("Empty trajectory positions")
    x, y, z = pts[-1]
    return float(x), float(y), float(z)


def compute_vln_metrics(
    gt: EpisodeGT,
    pred_positions_m: Iterable[Iterable[float]],
    success_radius_m: float = 20.0,
) -> dict:
    """
    Continuous-space SR/NE/SPL:
    - SR_i = 1[dist(final, goal) < success_radius]
    - NE_i = dist(final, goal)
    - SPL_i = SR_i * (L_i / max(L_i, P_i))
      where L_i is GT path length, P_i is predicted path length.
    """
    pts = [tuple(map(float, p)) for p in pred_positions_m]
    if len(pts) == 0:
        raise ValueError("Empty pred positions")
    final_pos = pts[-1]
    dx = final_pos[0] - gt.target_pos_m[0]
    dy = final_pos[1] - gt.target_pos_m[1]
    dz = final_pos[2] - gt.target_pos_m[2]
    ne = math.sqrt(dx * dx + dy * dy + dz * dz)
    sr = float(ne < success_radius_m)
    p_len = trajectory_length_m(pts)
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


def parse_task_test_positions(task_test_txt: Union[str, Path]) -> List[List[float]]:
    """
    Parse `DroneController/test/artifacts/current/task_test.txt` for a quick sanity-check.
    We use each step's End Position as a trajectory point.
    """
    task_test_txt = Path(task_test_txt)
    text = task_test_txt.read_text(encoding="utf-8")
    pos_re = re.compile(r"^\s*Position:\s*x=([-\d.]+),\s*y=([-\d.]+),\s*z=([-\d.]+)\s*$", re.M)

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


def _now_task_id() -> str:
    return time.strftime("%Y%m%d_%H%M%S", time.localtime())


if __name__ == "__main__":
    # Sanity-check example:
    dataset_root = Path("Datasets") / "vln"
    gt0 = load_gt_episode(dataset_root, idx=0)
    pred = parse_task_test_positions(Path("DroneController") / "test" / "artifacts" / "current" / "task_test.txt")
    if len(pred) == 0:
        raise SystemExit("No positions parsed from task_test.txt")
    metrics = compute_vln_metrics(gt0, pred_positions_m=pred, success_radius_m=20.0)
    print(metrics)

