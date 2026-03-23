import airsim

client = airsim.MultirotorClient()
print(client.getSettingsString())

print(client.listVehicles())