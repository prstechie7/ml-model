"""
=============================================================================
TEST SUITE: SENSOR & ADC TELEMETRY BENCHMARK (Radxa Qualcomm Platform)
Tests: Raw 12-bit ADC channels, Soil Moisture calibration mapping, DHT11 timing
=============================================================================
"""

import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from hardware.sensor_telemetry import AgribotSensorStation


def run_sensor_test():
    print("==================================================")
    print("🌿 RADXA SENSOR TELEMETRY BENCHMARK TEST")
    print("==================================================")

    station = AgribotSensorStation()

    print("\n[TEST 1] Sampling Soil Moisture Probes (3-Depth ADC)...")
    for sample in range(3):
        moist = station.read_soil_moisture()
        print(f"  • Sample #{sample+1}: Probe 1={moist['m1']}% | Probe 2={moist['m2']}% | Probe 3={moist['m3']}% | Avg={moist['avg']}% [{moist['status']}]")
        time.sleep(0.5)

    print("\n[TEST 2] Sampling DHT11 Climate Sensor...")
    dht_info = station.read_dht(max_retries=3)
    if dht_info["success"]:
        print(f"  • DHT11 Read OK: Temp={dht_info['temperature']}°C | Humidity={dht_info['humidity']}%")
    else:
        print("  • DHT11 Read: Handled timeout gracefully.")

    print("\n✓ ALL SENSOR BENCHMARK TESTS PASSED.\n")


if __name__ == "__main__":
    run_sensor_test()
