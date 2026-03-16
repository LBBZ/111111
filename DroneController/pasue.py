import airsim

client = airsim.MultirotorClient()
client.simPause(not client.simIsPause())