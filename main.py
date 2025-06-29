from sensors.pimoroni_bme680 import get_bme680_readings
from db.temperature_db import create_bme680_entry
import time


def main():
    while True:
        data = get_bme680_readings()
        print(f"Sensor Data: {data}")
        if data is None:
            print("Warning: Sensor data is None!")
            continue
        else:
            create_bme680_entry(
                data.temperature,
                data.humidity,
                data.pressure,
                data.gas_resistance,
            )
        time.sleep(3600)  # Sleep for 1 hour before the next reading


if __name__ == "__main__":
    main()
