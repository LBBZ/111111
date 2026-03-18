import airsim

client = airsim.MultirotorClient()

client.confirmConnection()

client.enableApiControl(True)

client.armDisarm(True)

client.takeoffAsync().join()

client.moveToPositionAsync(10,10, -53.36726, 5).join()
