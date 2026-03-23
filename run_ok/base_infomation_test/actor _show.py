import airsim

client = airsim.MultirotorClient()
client.simPause(False)

objs = client.simListSceneObjects()
print(len(objs))
print(objs[:20])

client.simPause(True)

pose = client.simGetObjectPose("Actor_1")
print(pose)