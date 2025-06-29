from flask import Flask, jsonify, request
from db.temperature_db import (
    read_entries,
    create_bme680_entry,
    create_entry_meta_data,
    update_entry_meta_data,
)

app = Flask(__name__)


# GET all BME680 readings with metadata
@app.route("/api/bme680_readings", methods=["GET"])
def get_readings():
    readings = read_entries()
    return jsonify(readings)


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


# POST a new BME680 reading
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


@app.route("/")
def index():
    return "Readings API is running!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
