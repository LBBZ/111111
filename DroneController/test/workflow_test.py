#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
workflow_test.py
用于启动完整的无人机 → 传感器 → Prompt → LLM → 动作执行流程
"""
from DroneController.airsim_client import AirSimClientSingleton
from DroneController.controller import DroneController

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
