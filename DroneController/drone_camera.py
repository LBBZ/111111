# drone_camera.py
import airsim
import numpy as np
import cv2

from airsim_client import AirSimClientSingleton

class DroneCamera:
    def __init__(self, vehicle_name: str = "keli"):
        self.client = AirSimClientSingleton().get_client()
        self.vehicle_name = vehicle_name

        # -------- 9 个摄像机名称 --------
        self.front_cam_id = "Front"
        self.back_cam_id = "Back"
        self.left_cam_id = "Left"
        self.right_cam_id = "Right"
        self.front_left_cam_id = "FrontLeft"
        self.front_right_cam_id = "FrontRight"
        self.back_left_cam_id = "BackLeft"
        self.back_right_cam_id = "BackRight"
        self.down_cam_id = "TopDown"

    def _get_image_by_id(self, cam_id: str):
        resp = self.client.simGetImages([
            airsim.ImageRequest(cam_id, airsim.ImageType.Scene, False, False)
        ], vehicle_name = self.vehicle_name)[0]

        if resp.height == 0:
            return None

        img1d = np.frombuffer(resp.image_data_uint8, dtype=np.uint8)
        img = img1d.reshape(resp.height, resp.width, 3)
        return img

    # -------- 原有三个接口 --------

    def capture_front(self):
        return self._get_image_by_id(self.front_cam_id)

    def capture_down(self):
        return self._get_image_by_id(self.down_cam_id)

    def capture_back(self):
        return self._get_image_by_id(self.back_cam_id)

    # -------- 新增六个方向 --------

    def capture_left(self):
        return self._get_image_by_id(self.left_cam_id)

    def capture_right(self):
        return self._get_image_by_id(self.right_cam_id)

    def capture_front_left(self):
        return self._get_image_by_id(self.front_left_cam_id)

    def capture_front_right(self):
        return self._get_image_by_id(self.front_right_cam_id)

    def capture_back_left(self):
        return self._get_image_by_id(self.back_left_cam_id)

    def capture_back_right(self):
        return self._get_image_by_id(self.back_right_cam_id)

    # -------- 一键拍摄 9 个方向 --------

    def capture_all(self):
        """
        返回 dict:
        {
            "Front": img,
            "Back": img,
            ...
        }
        """

        camera_ids = [
            self.front_cam_id,
            self.back_cam_id,
            self.left_cam_id,
            self.right_cam_id,
            self.front_left_cam_id,
            self.front_right_cam_id,
            self.back_left_cam_id,
            self.back_right_cam_id,
            self.down_cam_id
        ]

        responses = self.client.simGetImages([
            airsim.ImageRequest(cam, airsim.ImageType.Scene, False, False)
            for cam in camera_ids
        ], vehicle_name = self.vehicle_name)

        result = {}

        for cam, resp in zip(camera_ids, responses):
            if resp.height == 0:
                result[cam] = None
                continue

            img1d = np.frombuffer(resp.image_data_uint8, dtype=np.uint8)
            img = img1d.reshape(resp.height, resp.width, 3)
            result[cam] = img

        return result

    # -------- 通用保存接口（不变） --------

    @staticmethod
    def save_image(img, filename: str) -> bool:
        """
        通用保存接口：给你一张 numpy 图像，保存到文件
        """
        if img is None:
            return False
        cv2.imwrite(filename, img)
        return True
