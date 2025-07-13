from sys import path
import os

path.append(os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import pytz
import logging
from db.temperature_db import (
    read_entries,
    create_bme680_entry,
    create_entry_meta_data,
    update_entry_meta_data,
)
from sensors.openmetro import get_openmetro_readings


app = Flask(__name__)

# Configure logging to handle SSL errors more gracefully
logging.basicConfig(level=logging.INFO)

CORS(
    app,
    origins=["*"],  # Allow all origins for development
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    supports_credentials=True,
)


# Error handler for SSL/TLS connection attempts
@app.errorhandler(400)
def handle_bad_request(e):
    if hasattr(request, "data") and request.data.startswith(b"\x16\x03"):
        app.logger.warning(
            f"TLS/SSL connection attempt from {request.remote_addr}. Use HTTP instead of HTTPS."
        )
        return (
            jsonify(
                {
                    "error": "This server only accepts HTTP connections. Please use http:// instead of https://"
                }
            ),
            400,
        )
    return jsonify({"error": "Bad request"}), 400


@app.route("/")
def index():
    return "Readings API is running!"


# GET all BME680 readings with metadata a
@app.route("/api/bme680_readings", methods=["GET"])
def get_bme680_readings():
    start_date = request.args.get("startDate")
    end_date = request.args.get("endDate")

    print(f"Received request with startDate: {start_date}, endDate: {end_date}")

    if not start_date:
        return (
            jsonify({"error": "startDate query parameter is required"}),
            400,
        )

    transformed_readings = get_bme680_data(start_date, end_date)

    return transformed_readings


# TODO: update function names to be specific to BME680 readings
# POST a new BME680 reading
@app.route("/api/bme680_readings", methods=["POST"])
def create_reading():
    data = request.get_json()

    required_fields = ["temperature", "humidity", "pressure", "gas_resistance"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        create_bme680_entry(
            data["temperature"],
            data["humidity"],
            data["pressure"],
            data["gas_resistance"],
        )

        return jsonify({"message": "Create entry successful"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# POST a new meta_data reading
@app.route("/api/bme680_readings/meta_data", methods=["POST"])
def create_meta_data():
    data = request.get_json()

    # Validate input
    required_fields = ["reading_id", "ac", "converings", "notes"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        create_entry_meta_data(
            data["reading_id"], data["ac"], data["converings"], data["notes"]
        )
        return jsonify({"message": "Create entry successful"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# PUT to update an existing meta data entry
@app.route("/api/bme680_readings/meta_data/<int:entry_id>", methods=["PUT"])
def update_reading(entry_id):
    data = request.get_json()

    try:
        update_entry_meta_data(
            entry_id, data.get("ac"), data.get("converings"), data.get("notes")
        )

        return jsonify({"message": "Create entry successful"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# GET historical readings from Open-Meteo API
@app.route("/api/historical_readings", methods=["GET"])
def get_historical_readings(start_date=None, end_date=None):
    start_date = request.args.get("startDate")
    end_date = request.args.get("endDate")

    print(f"HIST- Received request with startDate: {start_date}, endDate: {end_date}")

    if not start_date or not end_date:
        return (
            jsonify({"error": "startDate & endDate query parameter is required"}),
            400,
        )

    try:
        historical_readings = get_openmetro_readings(start_date, end_date)
        return historical_readings
    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/api/all_readings", methods=["GET"])
def get_all_readings():
    start_date = request.args.get("startDate")
    end_date = request.args.get("endDate")

    if not start_date or not end_date:
        return (
            jsonify({"error": "startDate & endDate query parameter is required"}),
            400,
        )

    historical_readings = get_historical_readings(
        start_date,
        end_date,
    )
    bme680_readings = get_bme680_data(
        start_date,
        end_date,
    )

    if len(bme680_readings) > 0 and len(historical_readings) > 0:
        map_historical_data = {
            item["timestamp"][:13]: {
                "temp": item["historicalTemperature"],
                "humid": item["historicalHumidity"],
            }
            for item in historical_readings
        }

        # Merge sensorData with historical temperatures
        merged_data = []
        for item in bme680_readings:
            key = item["readingCreatedAtNearestHour"][:13]
            match = map_historical_data.get(key)
            merged_item = item.copy()
            merged_item["historicalTemperature"] = match["temp"]
            merged_item["historicalHumidity"] = match["humid"]
            merged_data.append(merged_item)

        return merged_data

    else:
        return []


def get_bme680_data(start_date, end_date):
    print(f"Received request with startDate: {start_date}, endDate: {end_date}")
    readings = read_entries(start_date, end_date)

    # Transform date to nearest hour for matching with other datasets
    for reading in readings:
        dt = datetime.fromisoformat(
            reading["reading_created_at"].replace("Z", "+00:00")
        )
        rounded = dt.replace(minute=0, second=0, microsecond=0)
        reading["reading_created_at_nearest_hour"] = rounded.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

    transformed_readings = [
        {
            "id": reading["reading_id"],
            "temperature": reading["temperature"],
            "humidity": reading["humidity"],
            "pressure": reading["pressure"],
            "readingCreatedAt": reading["reading_created_at"],
            "readingCreatedAtNearestHour": reading["reading_created_at_nearest_hour"],
        }
        for reading in readings
    ]
    return transformed_readings
    return []


def localize_datetime(utc_str):
    utc_time = datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    utc_time = utc_time.replace(tzinfo=pytz.utc)

    # Convert to Pacific Time (automatically handles PDT/PST)
    pacific = pytz.timezone("US/Pacific")
    pacific_time = utc_time.astimezone(pacific)

    # Format the result in the same ISO 8601 format
    formatted = pacific_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    return formatted


if __name__ == "__main__":
    # For HTTPS support, uncomment the next line and provide SSL certificate files
    # app.run(host="0.0.0.0", port=5000, debug=True, ssl_context='adhoc')

    # For HTTP only (current setup)
    app.run(host="0.0.0.0", port=5000, debug=True)
