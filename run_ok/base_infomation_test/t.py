import time

import airsim
import cv2
import numpy as np

vehicle_name = "keli"

def main():
    # 连接到 AirSim
    client = airsim.MultirotorClient()
    client.confirmConnection()
    print("连接到 AirSim 成功！")
    # 恢复仿真 
    client.simPause(False)

    # 解锁无人机
    client.enableApiControl(True, vehicle_name)
    client.armDisarm(True, vehicle_name)

    # 瞬移到指定位置
    target_position = airsim.Vector3r(0, 0, 0)
    client.simSetVehiclePose(airsim.Pose(target_position, airsim.Quaternionr(0, 0, 0, 1)), True, vehicle_name)
    print(f"瞬移到位置: {target_position}")

    # 等待一段时间以确保位置更新
    time.sleep(2)

    # 向上移动 20 米
    current_position = client.getMultirotorState(vehicle_name).kinematics_estimated.position
    new_position = airsim.Vector3r(current_position.x_val, current_position.y_val, current_position.z_val - 20)
    client.moveToPositionAsync(new_position.x_val, new_position.y_val, new_position.z_val, 5, vehicle_name = vehicle_name).join()
    print(f"向上移动 20 米到位置: {new_position}")

    # 等待一段时间以确保无人机稳定
    time.sleep(2)

    # 获取前视摄像头的图片
    responses = client.simGetImages([airsim.ImageRequest("0", airsim.ImageType.Scene, False, False)], vehicle_name)
    if responses:
        response = responses[0]
        # 将图像数据转换为 numpy 数组
        img1d = np.frombuffer(response.image_data_uint8, dtype=np.uint8)
        img_rgb = img1d.reshape(response.height, response.width, 3)

        # 保存图片到本地
        cv2.imwrite("../task_test_img/front_camera_image.png", img_rgb)
        print(f"图片已保存")
    else:
        print("未能获取前视摄像头的图片！")

    # 解除控制
    # client.armDisarm(False)
    # client.enableApiControl(False)
    print("测试完成！")
    # 暂停仿真 
    client.simPause(True)

if __name__ == "__main__":
    main()