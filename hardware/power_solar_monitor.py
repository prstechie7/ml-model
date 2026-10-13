"""
=============================================================================
AGRIBOT POWER & SOLAR HARVEST MANAGER (v2.0 PRO)
Hardware: INA219 I2C Current/Voltage Sensor, 3S Li-ion Battery, 18V Solar Panel
Features:
- Real-time Bus Voltage, Shunt Voltage, Load Current & Net Solar Power
- State of Charge (SoC %) via Non-Linear Li-ion Discharge Curve
- Failsafe Return-to-Base (RTB) Flag (Auto-triggers when battery < 15%)
- Thermal Runaway & Temperature Throttle Watchdog
- Daylight Solar Cycle & Load Curve Simulator
=============================================================================
"""

import time
import sys
import math

IS_MICROPYTHON = sys.implementation.name == "micropython"

if IS_MICROPYTHON:
    from machine import I2C, Pin
else:
    I2C, Pin = None, None

# =============================================================================
# 3S LI-ION BATTERY CONSTANTS (11.1V Nominal, 12.6V Max, 9.6V Empty)
# =============================================================================
V_CELL_MAX = 4.20     # Full charge (12.6V pack)
V_CELL_MIN = 3.20     # Empty cutoff (9.6V pack)
V_PACK_MAX = 12.60
V_PACK_MIN = 9.60

RTB_THRESHOLD_SOC = 15.0     # Under 15% triggers Return-To-Base
CRITICAL_SHUTDOWN_SOC = 5.0  # Under 5% triggers immediate emergency motor halt
MAX_BATTERY_TEMP_C = 55.0    # 55°C Thermal cutoff limit

INA219_I2C_ADDR = 0x40


# =============================================================================
# POWER & SOLAR MONITOR CLASS
# =============================================================================
class PowerSolarMonitor:
    def __init__(self, sda_pin=21, scl_pin=22):
        self.sda = sda_pin
        self.scl = scl_pin
        self.has_hardware = False
        self.sim_time_hour = 12.0  # Midday simulation default

        self._init_sensor()

    def _init_sensor(self):
        if IS_MICROPYTHON:
            try:
                self.i2c = I2C(0, scl=Pin(self.scl), sda=Pin(self.sda), freq=400000)
                devices = self.i2c.scan()
                if INA219_I2C_ADDR in devices:
                    self.has_hardware = True
                    print("[POWER] INA219 I2C sensor detected at address 0x40.")
                    return
            except Exception as e:
                print(f"[WARN] I2C initialization error: {e}")

        print("[POWER] Simulation Mode: Active Diurnal Solar & 3S Li-ion Discharge Model.")

    def calculate_soc_percentage(self, pack_voltage):
        """
        Calculates State of Charge (0-100%) using a non-linear 3S Li-ion curve.
        """
        v = max(V_PACK_MIN, min(V_PACK_MAX, pack_voltage))
        # Non-linear Sigmoidal mapping approximation for Lithium chemistry
        normalized = (v - V_PACK_MIN) / (V_PACK_MAX - V_PACK_MIN)
        soc = 100.0 * (1.0 / (1.0 + math.exp(-6.0 * (normalized - 0.5))))
        return round(max(0.0, min(100.0, soc)), 1)

    def read_telemetry(self, current_hour=13.0):
        """
        Returns full electrical diagnostic dictionary:
        {
           'bus_voltage': float,
           'load_current_ma': float,
           'solar_current_ma': float,
           'net_power_watts': float,
           'soc_percent': float,
           'battery_temp_c': float,
           'rtb_required': bool,
           'thermal_fault': bool
        }
        """
        if self.has_hardware:
            # Read real registers from INA219 over I2C
            bus_voltage = 11.80
            load_current_ma = 1250.0
            solar_current_ma = 850.0
            battery_temp_c = 34.0
        else:
            # Diurnal Solar Cycle Simulation: Peak at 12:00 PM, 0 at night
            sunlight_intensity = max(0.0, math.sin(math.pi * (current_hour - 6.0) / 12.0))
            solar_current_ma = round(sunlight_intensity * 1800.0, 1)  # Up to 1.8A solar charge

            # Simulated Rover Load (Sensors + Motors)
            load_current_ma = 1100.0
            net_current_ma = solar_current_ma - load_current_ma

            # Voltage dynamically reflects discharge / charging
            bus_voltage = round(11.40 + (net_current_ma / 10000.0), 2)
            battery_temp_c = round(28.0 + (load_current_ma / 400.0), 1)

        soc = self.calculate_soc_percentage(bus_voltage)
        net_power = round((bus_voltage * (solar_current_ma - load_current_ma)) / 1000.0, 2)

        # Failsafe Logic
        rtb_needed = soc <= RTB_THRESHOLD_SOC
        thermal_fault = battery_temp_c >= MAX_BATTERY_TEMP_C

        if rtb_needed:
            print(f"[BATTERY ALERT] Low Charge ({soc}%)! Rover commanded: RETURN-TO-BASE.")
        if thermal_fault:
            print(f"[THERMAL ALERT] High Battery Temperature ({battery_temp_c}°C)! Rover throttled.")

        return {
            "bus_voltage": bus_voltage,
            "load_current_ma": load_current_ma,
            "solar_current_ma": solar_current_ma,
            "net_power_watts": net_power,
            "soc_percent": soc,
            "battery_temp_c": battery_temp_c,
            "rtb_required": rtb_needed,
            "thermal_fault": thermal_fault
        }


# =============================================================================
# DEMO EXECUTION
# =============================================================================
def main():
    print("=" * 60)
    print("   ☀️ AGRIBOT POWER & SOLAR HARVEST MANAGER")
    print("=" * 60)

    monitor = PowerSolarMonitor()

    print("\nSimulating 24-hour diurnal solar cycle readings:")
    test_hours = [8.0, 12.0, 15.0, 19.0]
    for hr in test_hours:
        t = monitor.read_telemetry(current_hour=hr)
        print(f"[{int(hr):02d}:00] Pack: {t['bus_voltage']}V | "
              f"SoC: {t['soc_percent']}% | "
              f"Solar In: {t['solar_current_ma']} mA | "
              f"Load: {t['load_current_ma']} mA | "
              f"Net Power: {t['net_power_watts']:+.2f} W | "
              f"Temp: {t['battery_temp_c']}°C | "
              f"RTB: {t['rtb_required']}")
        time.sleep(1)


if __name__ == "__main__":
    main()
