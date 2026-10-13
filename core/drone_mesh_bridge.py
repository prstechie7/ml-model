"""
=============================================================================
AGRIBOT DRONE MESH BRIDGE (v2.0 PRO)
Hardware/Protocol: MQTT / WebSocket Multi-Agent Agricultural Coordinator
Features:
- Aerial-to-Ground Scouting Synchronization (UAV Drone -> Rover)
- Drone Outlier & Multispectral NDVI Hotspot Ingestion
- Dynamic High-Priority Waypoint Insertion (Preempts Rover Mission Queue)
- Threaded Async Listener for Low-Latency Telemetry Streaming
- Built-in Aerial Anomaly Simulator with Configurable Intervals
=============================================================================
"""

import time
import json
import threading
import random

try:
    import paho.mqtt.client as mqtt
    PAHO_AVAILABLE = True
except ImportError:
    PAHO_AVAILABLE = False


# =============================================================================
# DEFAULT BROKER & TOPIC DEFINITIONS
# =============================================================================
DEFAULT_MQTT_BROKER = "broker.hivemq.com"
DEFAULT_MQTT_PORT = 1883
TOPIC_DRONE_ANOMALY = "agribot/drone/anomaly/hotspot"
TOPIC_ROVER_ACK = "agribot/rover/mission/ack"


# =============================================================================
# DRONE MESH BRIDGE CLASS
# =============================================================================
class DroneMeshBridge:
    def __init__(self, waypoint_navigator=None, broker=DEFAULT_MQTT_BROKER, port=DEFAULT_MQTT_PORT):
        self.nav = waypoint_navigator
        self.broker = broker
        self.port = port
        self.client = None
        self.is_connected = False
        self.hotspots_received = []

        self._init_network()

    def _init_network(self):
        if PAHO_AVAILABLE:
            try:
                self.client = mqtt.Client(client_id="Agribot_Ground_Rover_Bridge")
                self.client.on_connect = self._on_connect
                self.client.on_message = self._on_message
                self.client.connect_async(self.broker, self.port, 60)
                self.client.loop_start()
                print(f"[DRONE-BRIDGE] Connected to MQTT Drone Mesh on {self.broker}:{self.port}")
                return
            except Exception as e:
                print(f"[WARN] Failed to start MQTT client: {e}")

        print("[DRONE-BRIDGE] Simulation Mode: Background Aerial Scouting Stream Active.")
        self._start_simulation_thread()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.is_connected = True
            self.client.subscribe(TOPIC_DRONE_ANOMALY)
            print(f"[DRONE-BRIDGE] Subscribed to aerial scouting topic: {TOPIC_DRONE_ANOMALY}")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            self.ingest_aerial_anomaly(payload)
        except Exception as e:
            print(f"[ERROR] Failed to parse drone payload: {e}")

    def ingest_aerial_anomaly(self, anomaly_payload):
        """
        Receives an aerial hotspot from the drone:
        {
          "uav_id": "DRONE-01",
          "latitude": float,
          "longitude": float,
          "ndvi_index": float (e.g. 0.22 = severe stress),
          "severity": "CRITICAL" | "MODERATE",
          "anomaly_type": "crop_blight" | "water_stress"
        }
        """
        lat = anomaly_payload.get("latitude")
        lon = anomaly_payload.get("longitude")
        severity = anomaly_payload.get("severity", "MODERATE")
        atype = anomaly_payload.get("anomaly_type", "unknown")
        ndvi = anomaly_payload.get("ndvi_index", 0.0)

        print(f"\n🚨 [AERIAL OUTLIER DETECTED BY UAV] Drone ID: {anomaly_payload.get('uav_id', 'DRONE-01')}")
        print(f"  • Coordinate: ({lat:.6f}, {lon:.6f}) | Type: {atype.upper()} | NDVI: {ndvi}")

        self.hotspots_received.append(anomaly_payload)

        # Dynamic Waypoint Injection
        if self.nav and hasattr(self.nav, "waypoints"):
            # Insert at the immediate head of the line (High Priority Task Preemption)
            target_coord = (lat, lon)
            self.nav.waypoints.insert(self.nav.current_wp_idx, target_coord)
            print(f"  └─ Dynamic Route Injected! Rover diverted immediately to investigate hotspot.")

        return True

    def _start_simulation_thread(self):
        """Simulates periodic aerial drone surveys injecting anomalies."""
        def sim_worker():
            sample_anomalies = [
                {"uav_id": "UAV-SCOUT-9", "latitude": 22.720150, "longitude": 75.858200, "ndvi_index": 0.18, "severity": "CRITICAL", "anomaly_type": "fungal_yellowing"},
                {"uav_id": "UAV-SCOUT-9", "latitude": 22.719850, "longitude": 75.857900, "ndvi_index": 0.25, "severity": "MODERATE", "anomaly_type": "water_deficit"}
            ]
            for item in sample_anomalies:
                time.sleep(3)
                self.ingest_aerial_anomaly(item)

        t = threading.Thread(target=sim_worker, daemon=True)
        t.start()


# =============================================================================
# DEMO EXECUTION
# =============================================================================
def main():
    print("=" * 60)
    print("   🛸 AGRIBOT DRONE-TO-ROVER MESH COORDINATOR")
    print("=" * 60)

    # Mock navigator object with waypoints
    class MockNavigator:
        def __init__(self):
            self.waypoints = [(22.7192, 75.8572), (22.7208, 75.8572)]
            self.current_wp_idx = 0

    nav = MockNavigator()
    bridge = DroneMeshBridge(waypoint_navigator=nav)

    print("\nInitial Rover Waypoint Queue:", nav.waypoints)
    print("Awaiting drone reconnaissance scouting pings...\n")

    # Run for 7 seconds to display simulated anomaly injection
    time.sleep(7)
    print("\nUpdated Rover Waypoint Queue after Drone Injections:")
    for i, wp in enumerate(nav.waypoints):
        print(f"  [{i + 1}] Lat: {wp[0]:.6f}, Lon: {wp[1]:.6f}")


if __name__ == "__main__":
    main()
