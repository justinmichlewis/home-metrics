import sqlite3
import os
from typing import Optional
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data.db")


def create_bme680_entry(
    temperature: float, humidity: float, pressure: float, gas_resistance: float
):
    """Create a new entry in the database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO bme680_readings ( temperature, humidity, pressure, gas_resistance) VALUES ( ?, ?, ?, ?)",
        (temperature, humidity, pressure, gas_resistance),
    )
    conn.commit()
    conn.close()


def read_entries():
    """Read all entries from the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.execute(
        """
        SELECT
            b.reading_id,
            b.temperature,
            b.humidity,
            b.pressure,
            b.gas_resistance,
            b.created_at AS reading_created_at,
            e.entry_id,
            e.ac,
            e.converings,
            e.notes,
            e.created_at AS meta_data_created_at
        FROM bme680_readings AS b
        LEFT JOIN entry_meta_data AS e
        ON b.reading_id = e.reading_id
        ORDER BY b.reading_id DESC
        LIMIT 100
    """
    )
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows


def create_entry_meta_data(reading_id, ac, converings, notes):
    """Create a new entry in the entry_meta_data table."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO entry_meta_data (reading_id, ac, converings, notes) VALUES (?, ?, ?, ?)",
        (reading_id, ac, converings, notes),
    )
    conn.commit()
    conn.close()


def update_entry_meta_data(
    entry_id: int,
    ac: Optional[int] = None,
    converings: Optional[int] = None,
    notes: Optional[str] = None,
):
    """Update selected fields of an existing entry in the entry_meta_data table."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    fields = []
    values = []

    if ac is not None:
        fields.append("ac = ?")
        values.append(ac)
    if converings is not None:
        fields.append("converings = ?")
        values.append(converings)
    if notes is not None:
        fields.append("notes = ?")
        values.append(notes)

    if not fields:
        print("Nothing to update.")
        return

    values.append(entry_id)
    query = f"UPDATE entry_meta_data SET {', '.join(fields)} WHERE entry_id = ?"
    c.execute(query, values)
    conn.commit()
    conn.close()


def read_entry_meta_data():
    """Read all entries from the entry_meta_data table."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM entry_meta_data")
    rows = c.fetchall()
    conn.close()
    return rows


###########################################################
#                    TABLE DEFINITIONS                    #
###########################################################

# CREATE TABLE entry_meta_data (
#     entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
#     reading_id INTEGER,
#     ac INTEGER,
#     converings INTEGER,
#     notes TEXT,
#     created_at TEXT DEFAULT (STRFTIME('%Y-%m-%dT%H:%M:%SZ', 'NOW')),
#     FOREIGN KEY (reading_id) REFERENCES bme680_readings(reading_id)
# );


# CREATE TABLE bme680_readings (
#     reading_id INTEGER PRIMARY KEY AUTOINCREMENT,
#     temperature REAL,
#     humidity REAL,
#     pressure REAL,
#     gas_resistance REAL,
#     created_at TEXT DEFAULT (STRFTIME('%Y-%m-%dT%H:%M:%SZ', 'NOW'))
# );
