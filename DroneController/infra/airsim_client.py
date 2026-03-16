import threading

import airsim


class AirSimClientSingleton:
    _client = None
    _lock = threading.Lock()

    def __new__(cls, vehicle_name="keli"):
        if cls._client is None:
            with cls._lock:
                if cls._client is None:
                    print(f"[{threading.current_thread().name}] Planning Client.")
                    client = airsim.MultirotorClient()
                    client.confirmConnection()
                    client.enableApiControl(True, vehicle_name)
                    client.armDisarm(True, vehicle_name)
                    client.simPause(False)
                    client.takeoffAsync().join()
                    client.simPause(True)
                    cls._client = client
        return cls._client
