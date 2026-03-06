# 注意事项
- 本文件用于了解项目信息, 在完成具体任务以前无需去读取以下文本中提到的文件内容
- 世界坐标系 z 轴向下为正方向
- others/settings 中设置了初始化的位置会重置无人机的世界原点, 无人机初始化在哪里对无人机而言哪里就是世界原点

# 项目目标
- 本项目利用原项目的数据集和评价系统去构建一个无人机路径规划系统, 初始化无人机位置, 给予无人机目标, 初始化将周围的信息给大模型, 大模型来分析任务目标来生成阶段性的任务, 每次移动后都重新获取周围信息进行下一步规划.

# 本项目的代码
- 本项目的代码完全位于目录 DroneController 下, 本项目的代码目前都是以 settings 为准的
- 包含相机功能, DroneCamera
    - 相机功能能够获取 9 个方向的 RGB img, Depth img, Depth npy（Front/Back/Left/Right/四个斜向/TopDown）
    - capture_all 函数可以一键获取 9 个方向的所有图像
- 移动功能, DroneMotion
    - 包含 平移：move_forward(d) / move_left(d) / move_right(d) / move_up(d) ...（单位米）
    - 转向：turn_left(angle_deg) / turn_right(angle_deg)（角度可控）
- init_img.py 和 test_runner.py 均是测试文件
- vln_metrics.py 是 SPL/NE/SR 准度计算文件, 目前还未验证受否能够使用

# 原项目代码
- prompts 目录下, embodied_tasks.py, embodied_vln.py, utils.py 均是原项目代码
- 其余部分的代码无效或者不重要, 不用在意
- Datasets 目录下, 为原作者提供的测试数据集, 用作  SPL/NE/SR  精度计算, 本项目同样使用这些数据集. 目前数据集给出的数据如何使用还在实验中

# 给 Agent 的指令版（必读）

## 总原则
- 本仓库有两套栈：**优先用 `DroneController/` 做闭环控制与采集**；需要对齐原 benchmark/论文流程时才看 `embodied_vln.py` + `vln/`。
- 统一口径：**AirSim 世界坐标 = NED，单位米 m（z 向下为正；上升= z 变小）**。任何来自数据集/Unreal 的坐标先确认是否为 cm，必要时 `/100` 转 m。

## 1) 环境/配置（强约束）
- AirSim settings：`others/settings.json`
  - `DefaultVehicle` = `keli`（`DroneController` 也默认用 `"keli"`，必须一致）
  - 初始 `X/Y/Z` 在 settings 里写死，别把它当“(0,0,0) 原点”
  - 9 向相机名固定为：`Front/Back/Left/Right/FrontLeft/FrontRight/BackLeft/BackRight/TopDown`（`DroneController/DroneCamera` 依赖这些名字）

## 2) 推荐的最小验证链路（按顺序做）
- **先验证观测**：跑 `DroneController/init_img.py`
  - 入口：`capture_views_at_pose(x,y,z,yaw_deg)`：瞬移到 pose → 拍 9 张 RGB + 9 张 Depth（npy+png）
- **再验证运动闭环**：跑 `DroneController/test_runner.py`
  - 会随机动作序列，记录每步起止位姿并保存观测（用于 sanity check）

## 3) 自研控制栈（DroneController）接口语义
- 相机：`DroneController/drone_camera.py`
  - `capture_all()`：一次取 9 向 RGB
  - `capture_all_depth()`：一次取 9 向 Depth（float32，单位米）
- 运动：`DroneController/drone_motion.py`
  - 平移：`move_forward(d)` / `move_left(d)` / `move_up(d)` ...（单位 m）
  - 转向：`turn_left(angle_deg)` / `turn_right(angle_deg)`（角度制）
  - 注意：`move_up(d)` 实现是 `z -= d`（NED）
- 连接：`DroneController/airsim_client.py`
  - 单例会 confirm/arm/takeoff，并可能 pause；不要重复创建一堆 client

## 4) 原作者 VLN 栈（仅参考/对齐指标）
- 入口：`embodied_vln.py`
  - 数据：`Datasets/vln/start_loc.txt` + `Datasets/vln/label/*.csv`
  - start_loc 位置按 cm 读入，代码里会 `/100` 转 m；且有 `start_pos[2] = -start_pos[2]` 的坐标处理（别和 `DroneController` 的坐标口径混在一起）
  - 动作是离散的（stop/forth/left/right/up/down 等），并且相机接口用的是 cameraID `"0"`/`"3"` 这套（不要和 9 向相机名混用）

## 5) 指标评测（推荐对自研轨迹用）
- `DroneController/vln_metrics.py`：
  - 读 `Datasets/vln` 的 GT（start_loc + label）
  - 给一条预测轨迹 `positions(m)` → 输出 `SR/NE/SPL`（success_radius 默认 20m）
  - 自研系统推荐：执行→记录轨迹点(m)→丢给 `compute_vln_metrics(...)`

## 6) 常见坑（禁止踩）
- **相机名 vs cameraID**：`DroneController` 用 `Front/.../TopDown`；原 VLN 常用 `"0"/"3"`，别混。
- **vehicle_name**：统一 `"keli"`（`run_ok/keyboard_control.py` 里 `vehicle_name=""` 需要手填，否则可能控不到目标机体）
- **数据集路径大小写**：仓库根 README 用 `Datasets/...`；`embodied_tasks.py` 里写 `dataset/...`（照抄会找不到文件）
- **坐标系**：NED 的 z 方向与直觉相反；Unreal(cm) 与 AirSim(m) 要明确换算