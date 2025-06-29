import bme680
import time

# Create a sensor object using I2C port 1, address 0x76
sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)

# Optional configuration
sensor.set_humidity_oversample(bme680.OS_2X)
sensor.set_pressure_oversample(bme680.OS_4X)
sensor.set_temperature_oversample(bme680.OS_8X)
sensor.set_filter(bme680.FILTER_SIZE_3)
sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)

# Set gas sensor parameters (recommended values)
sensor.set_gas_heater_temperature(320)
sensor.set_gas_heater_duration(150)
sensor.select_gas_heater_profile(0)

print("Reading BME680 sensor values...")


class SensorData:
    def __init__(self, temperature, humidity, pressure, gas_resistance):
        self.temperature = temperature
        self.humidity = humidity
        self.pressure = pressure
        self.gas_resistance = gas_resistance

    def __str__(self):
        return f"{self.temperature:.2f}, {self.humidity:.2f}, {self.pressure:.2f}, {self.gas_resistance:.2f}"


def convert_celsius_to_fahrenheit(celsius):
    """Convert Celsius to Fahrenheit."""
    return (celsius * 9 / 5) + 32


def get_bme680_readings():
    if sensor.get_sensor_data():
        return SensorData(
            temperature=sensor.data.temperature,
            humidity=sensor.data.humidity,
            pressure=sensor.data.pressure / 1000,  # Convert hPa to kPa
            gas_resistance=sensor.data.gas_resistance / 1000,  # Convert Ohms to kΩ
        )


# while True:
#     data = get_bme680_readings()
#     print(f"Sensor Data: {data}")
#     time.sleep(2)
