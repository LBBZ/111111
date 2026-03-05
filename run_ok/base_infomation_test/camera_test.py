import os
from time import sleep

import airsim
import cv2
import numpy as np

print("User:", os.getlogin())
print("Expected settings path:")
print(os.path.join(os.path.expanduser("~"), "Documents", "AirSim", "settings.json"))

client = airsim.MultirotorClient()
client.simPause(False)

# 瞬移到指定位置
target_position = airsim.Vector3r(0, 0, 0)
client.simSetVehiclePose(airsim.Pose(target_position, airsim.Quaternionr(0, 0, 0, 1)), True)
print(f"瞬移到位置: {target_position}")

sleep(0.5)
client.simPause(True)

client.simGetWorldExtents()
# # 这是默认的
# responses = client.simGetImages([
#     airsim.ImageRequest("0", airsim.ImageType.Scene, False, False),
#     airsim.ImageRequest("1", airsim.ImageType.Scene, False, False),
#     airsim.ImageRequest("2", airsim.ImageType.Scene, False, False),
#     airsim.ImageRequest("3", airsim.ImageType.Scene, False, False),
#     airsim.ImageRequest("4", airsim.ImageType.Scene, False, False),
#
# ])
# print(type(responses))
# for idx in range(len(responses)):
#     response = responses[idx]
#     # 将图像数据转换为 numpy 数组
#     img1d = np.frombuffer(response.image_data_uint8, dtype=np.uint8)
#     img_rgb = img1d.reshape(response.height, response.width, 3)
#
#     # 保存图片到本地
#     cv2.imwrite(str(idx) + ".png", img_rgb)

# 这是默认的
responses = client.simGetImages([
    airsim.ImageRequest("Front", airsim.ImageType.Scene, False, False),
    airsim.ImageRequest("Back", airsim.ImageType.Scene, False, False),
    airsim.ImageRequest("Left", airsim.ImageType.Scene, False, False),
    airsim.ImageRequest("Right", airsim.ImageType.Scene, False, False),
    airsim.ImageRequest("FrontLeft", airsim.ImageType.Scene, False, False),
    airsim.ImageRequest("FrontRight", airsim.ImageType.Scene, False, False),
    airsim.ImageRequest("BackLeft", airsim.ImageType.Scene, False, False),
    airsim.ImageRequest("BackRight", airsim.ImageType.Scene, False, False),
    airsim.ImageRequest("TopDown", airsim.ImageType.Scene, False, False),

])
print(type(responses))
for idx in range(len(responses)):
    response = responses[idx]
    # 将图像数据转换为 numpy 数组
    img1d = np.frombuffer(response.image_data_uint8, dtype=np.uint8)
    img_rgb = img1d.reshape(response.height, response.width, 3)

    # 保存图片到本地
    cv2.imwrite("new_" + str(idx) + ".png", img_rgb)