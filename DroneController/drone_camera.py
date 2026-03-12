# drone_camera.py
from typing import Optional

import airsim
import numpy as np
import cv2
import os

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

    def _get_depth_by_id(self, cam_id: str, depth_type: int = airsim.ImageType.DepthPlanar):
        resp = self.client.simGetImages([
            airsim.ImageRequest(cam_id, depth_type, True, False)
        ], vehicle_name = self.vehicle_name)[0]

        if resp.height == 0:
            return None

        depth1d = np.array(resp.image_data_float, dtype=np.float32)
        if depth1d.size != resp.height * resp.width:
            return None
        depth = depth1d.reshape(resp.height, resp.width)
        return depth

    def _get_seg_by_id(self, cam_id: str, seg_type: int = airsim.ImageType.Segmentation):
        resp = self.client.simGetImages([
            airsim.ImageRequest(cam_id, seg_type, False, False)
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

    # -------- Depth 拍摄接口 --------

    def capture_front_depth(self, depth_type: int = airsim.ImageType.DepthPlanar):
        return self._get_depth_by_id(self.front_cam_id, depth_type=depth_type)

    def capture_down_depth(self, depth_type: int = airsim.ImageType.DepthPlanar):
        return self._get_depth_by_id(self.down_cam_id, depth_type=depth_type)

    def capture_back_depth(self, depth_type: int = airsim.ImageType.DepthPlanar):
        return self._get_depth_by_id(self.back_cam_id, depth_type=depth_type)

    def capture_left_depth(self, depth_type: int = airsim.ImageType.DepthPlanar):
        return self._get_depth_by_id(self.left_cam_id, depth_type=depth_type)

    def capture_right_depth(self, depth_type: int = airsim.ImageType.DepthPlanar):
        return self._get_depth_by_id(self.right_cam_id, depth_type=depth_type)

    def capture_front_left_depth(self, depth_type: int = airsim.ImageType.DepthPlanar):
        return self._get_depth_by_id(self.front_left_cam_id, depth_type=depth_type)

    def capture_front_right_depth(self, depth_type: int = airsim.ImageType.DepthPlanar):
        return self._get_depth_by_id(self.front_right_cam_id, depth_type=depth_type)

    def capture_back_left_depth(self, depth_type: int = airsim.ImageType.DepthPlanar):
        return self._get_depth_by_id(self.back_left_cam_id, depth_type=depth_type)

    def capture_back_right_depth(self, depth_type: int = airsim.ImageType.DepthPlanar):
        return self._get_depth_by_id(self.back_right_cam_id, depth_type=depth_type)

    def capture_all_depth(self, depth_type: int = airsim.ImageType.DepthPlanar):
        """
        返回 dict:
        {
            "Front": depth(HxW,float32, meters),
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
            airsim.ImageRequest(cam, depth_type, True, False)
            for cam in camera_ids
        ], vehicle_name = self.vehicle_name)

        result = {}
        for cam, resp in zip(camera_ids, responses):
            if resp.height == 0:
                result[cam] = None
                continue
            depth1d = np.array(resp.image_data_float, dtype=np.float32)
            if depth1d.size != resp.height * resp.width:
                result[cam] = None
                continue
            result[cam] = depth1d.reshape(resp.height, resp.width)

        return result

    # -------- Segmentation 拍摄接口 --------

    def capture_front_seg(self, seg_type: int = airsim.ImageType.Segmentation):
        return self._get_seg_by_id(self.front_cam_id, seg_type=seg_type)

    def capture_down_seg(self, seg_type: int = airsim.ImageType.Segmentation):
        return self._get_seg_by_id(self.down_cam_id, seg_type=seg_type)

    def capture_back_seg(self, seg_type: int = airsim.ImageType.Segmentation):
        return self._get_seg_by_id(self.back_cam_id, seg_type=seg_type)

    def capture_left_seg(self, seg_type: int = airsim.ImageType.Segmentation):
        return self._get_seg_by_id(self.left_cam_id, seg_type=seg_type)

    def capture_right_seg(self, seg_type: int = airsim.ImageType.Segmentation):
        return self._get_seg_by_id(self.right_cam_id, seg_type=seg_type)

    def capture_all_seg(self, seg_type: int = airsim.ImageType.Segmentation):
        camera_ids = [
            self.front_cam_id,
            self.back_cam_id,
            self.left_cam_id,
            self.right_cam_id,
            self.down_cam_id
        ]

        responses = self.client.simGetImages([
            airsim.ImageRequest(cam, seg_type, False, False)
            for cam in camera_ids
        ], vehicle_name=self.vehicle_name)

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

    # -------- Depth 保存接口 --------

    @staticmethod
    def save_depth_data(depth_m, filename: str) -> bool:
        """
        保存深度原始数据（单位：米）。推荐扩展名：.npy
        """
        if depth_m is None:
            return False
        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
        np.save(filename, np.asarray(depth_m, dtype=np.float32))
        return True

    @staticmethod
    def save_depth_image(depth_m, filename: str, *, max_depth_m: Optional[float] = 100.0) -> bool:
        """
        保存深度可视化图（16-bit PNG，单位：毫米）。
        - depth_m: HxW float32，单位米
        - max_depth_m: 用于裁剪上限；None 表示不裁剪（可能溢出 16-bit）
        """
        if depth_m is None:
            return False

        depth = np.asarray(depth_m, dtype=np.float32)
        depth = np.nan_to_num(depth, nan=0.0, posinf=0.0, neginf=0.0)
        depth = np.maximum(depth, 0.0)

        if max_depth_m is not None:
            depth = np.minimum(depth, float(max_depth_m))

        depth_mm = np.round(depth * 1000.0).astype(np.uint32)
        depth_mm = np.clip(depth_mm, 0, 65535).astype(np.uint16)

        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
        return bool(cv2.imwrite(filename, depth_mm))

    # -------- Segmentation 保存接口 --------
    @staticmethod
    def save_segmentation_vis(seg_rgb, filename: str) -> bool:
        if seg_rgb is None:
            return False
        cv2.imwrite(filename, seg_rgb)
        return True

    @staticmethod
    def save_segmentation_id(seg_rgb, filename: str) -> bool:
        if seg_rgb is None:
            return False
        id_mask = seg_rgb[:, :, 0]  # R 通道 = ID
        cv2.imwrite(filename, id_mask)
        return True

    @staticmethod
    def save_segmentation_npy(seg_rgb, filename: str) -> bool:
        if seg_rgb is None:
            return False
        id_mask = seg_rgb[:, :, 0].astype(np.uint16)
        np.save(filename, id_mask)
        return True

    @staticmethod
    def save_segmentation_tiff(seg_rgb, filename: str) -> bool:
        if seg_rgb is None:
            return False
        id_mask = seg_rgb[:, :, 0].astype(np.uint16)
        cv2.imwrite(filename, id_mask)
        return True



