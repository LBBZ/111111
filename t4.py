import os
import airsim
import cv2
import numpy as np

print("User:", os.getlogin())
print("Expected settings path:")
print(os.path.join(os.path.expanduser("~"), "Documents", "AirSim", "settings.json"))

client = airsim.MultirotorClient()



client.simGetWorldExtents()
responses = client.simGetImages([
    airsim.ImageRequest("0", airsim.ImageType.Scene, False, False),
    airsim.ImageRequest("1", airsim.ImageType.Scene, False, False),
    airsim.ImageRequest("2", airsim.ImageType.Scene, False, False),
    airsim.ImageRequest("3", airsim.ImageType.Scene, False, False),
    airsim.ImageRequest("4", airsim.ImageType.Scene, False, False),

])
print(type(responses))
for idx in range(len(responses)):
    response = responses[idx]
    # 将图像数据转换为 numpy 数组
    img1d = np.frombuffer(response.image_data_uint8, dtype=np.uint8)
    img_rgb = img1d.reshape(response.height, response.width, 3)

    # 保存图片到本地
    cv2.imwrite(str(idx) + ".png", img_rgb)
