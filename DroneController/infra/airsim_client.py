import threading

import airsim


class AirSimClientSingleton:
    """Thread-safe singleton for AirSim client."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, vehicle_name="keli"):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    print(f"[{threading.current_thread().name}] Planning Client.")
                    cls._instance = super(AirSimClientSingleton, cls).__new__(cls)
                    cls._instance._init_client(vehicle_name)
        return cls._instance

    def _init_client(self, vehicle_name):
        self.client = airsim.MultirotorClient()
        self.client.confirmConnection()
        self.client.enableApiControl(True, vehicle_name)
        self.client.armDisarm(True, vehicle_name)
        self.client.simPause(False)
        self.client.takeoffAsync().join()
        self.client.simPause(True)

    def get_client(self):
        return self.client
