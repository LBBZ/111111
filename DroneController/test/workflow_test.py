#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
workflow_test.py
用于启动完整的无人机 → 传感器 → Prompt → LLM → 动作执行流程
"""
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from DroneController.infra.airsim_client import AirSimClientSingleton
from DroneController.core.controller import DroneController

def main():
    print("=== Drone Workflow Test Started ===")

    # ---------------------------------------------------------
    # 初始化控制器 (DroneMotion 和 DroneCamera 在内部初始化)
    # ---------------------------------------------------------
    AirSimClientSingleton()
    controller = DroneController()

    # ---------------------------------------------------------
    # 启动主流程
    # ---------------------------------------------------------
    controller.run()

    print("=== Drone Workflow Test Finished ===")


if __name__ == "__main__":
    main()
