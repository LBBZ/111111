# drone_camera.py
import airsim
import numpy as np
import cv2

class DroneCamera:
    def __init__(self, vehicle_name: str = ""):
        self.client = airsim.MultirotorClient()
        self.client.confirmConnection()
        self.vehicle_name = vehicle_name

        # 这里约定摄像头 ID 映射，你可以按你那套：
        # 0: 前视, 3: 俯视, 4: 后视
        self.front_cam_id = "2"
        self.down_cam_id = "3"
        self.back_cam_id = "4"

    def _get_image_by_id(self, cam_id: str):
        resp = self.client.simGetImages([
            airsim.ImageRequest(cam_id, airsim.ImageType.Scene, False, False)
        ])[0]

        if resp.height == 0:
            return None

        img1d = np.frombuffer(resp.image_data_uint8, dtype=np.uint8)
        img = img1d.reshape(resp.height, resp.width, 3)
        return img

    # -------- 三个拍照接口 --------

    def capture_front(self):
        """返回前视图像 (numpy array)"""
        return self._get_image_by_id(self.front_cam_id)

    def capture_down(self):
        """返回俯视图像 (numpy array)"""
        return self._get_image_by_id(self.down_cam_id)

    def capture_back(self):
        """返回后视图像 (numpy array)"""
        return self._get_image_by_id(self.back_cam_id)

    # -------- 通用保存接口 --------

    @staticmethod
    def save_image(img, filename: str) -> bool:
        """
        通用保存接口：给你一张 numpy 图像，保存到文件
        """
        if img is None:
            return False
        cv2.imwrite(filename, img)
        return True
