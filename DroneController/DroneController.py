import airsim
import numpy as np
import cv2
import time

class DroneController:
    def __init__(self, vehicle_name=""):
        self.client = airsim.MultirotorClient()
        self.client.confirmConnection()
        self.client.enableApiControl(True, vehicle_name)
        self.client.armDisarm(True, vehicle_name)
        self.vehicle_name = vehicle_name

    # -------------------------
    #  Movement
    # -------------------------
    def move(self, vx=0, vy=0, vz=0, yaw_rate=0, duration=0.2):
        """
        Body frame movement.
        vx: forward/backward
        vy: left/right
        vz: up/down
        yaw_rate: rotation speed (deg/s)
        """
        self.client.moveByVelocityBodyFrameAsync(
            vx, vy, vz, duration,
            airsim.YawMode(is_rate=True, yaw_or_rate=yaw_rate),
            vehicle_name=self.vehicle_name
        ).join()

    def rotate(self, yaw_deg):
        """Rotate drone by yaw_deg degrees."""
        self.client.rotateByYawRateAsync(yaw_deg, 1).join()

    def move_to(self, x, y, z):
        """Absolute movement."""
        self.client.moveToPositionAsync(x, y, z, 3).join()

    # -------------------------
    #  Camera
    # -------------------------
    def get_image(self, cam_id=0):
        """Return RGB numpy array."""
        response = self.client.simGetImages([
            airsim.ImageRequest(str(cam_id), airsim.ImageType.Scene, False, False)
        ])[0]

        if response.height == 0:
            return None

        img1d = np.frombuffer(response.image_data_uint8, dtype=np.uint8)
        img = img1d.reshape(response.height, response.width, 3)
        return img

    def save_image(self, cam_id, filename):
        img = self.get_image(cam_id)
        if img is not None:
            cv2.imwrite(filename, img)
            return True
        return False

