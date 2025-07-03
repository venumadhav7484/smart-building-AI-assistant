"""Load public HVAC sensor history CSV into Postgres.

Expects a CSV with columns:
    timestamp,equipment_id,temperature,vibration,pressure

Example usage:
    USE_PGVECTOR=true PG_CONN=postgresql+psycopg2://pguser:pgpass@localhost:5432/building_ai \
    python scripts/load_sensor_history.py data/ashrae_building.csv
"""
from __future__ import annotations

import csv
import os
import sys
from datetime import datetime
from pathlib import Path

import psycopg2


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS sensor_history (
    timestamp TIMESTAMPTZ NOT NULL,
    equipment_id TEXT NOT NULL,
    temperature REAL,
    vibration REAL,
    pressure REAL
);
"""

INSERT_SQL = """
INSERT INTO sensor_history (timestamp, equipment_id, temperature, vibration, pressure)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT DO NOTHING;
"""

def load_csv(path: Path, conn_str: str) -> int:
    with psycopg2.connect(conn_str) as conn, conn.cursor() as cur:
        cur.execute(CREATE_TABLE_SQL)
        inserted = 0
        with path.open() as f:
            reader = csv.DictReader(f)
            for row in reader:
                ts = datetime.fromisoformat(row["timestamp"])
                cur.execute(
                    INSERT_SQL,
                    (
                        ts,
                        row["equipment_id"],
                        float(row.get("temperature", "nan")),
                        float(row.get("vibration", "nan")),
                        float(row.get("pressure", "nan")),
                    ),
                )
                inserted += 1
        return inserted


def _cli():
    if len(sys.argv) != 2:
        print("Usage: python scripts/load_sensor_history.py path/to/file.csv", file=sys.stderr)
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        print(f"File {csv_path} not found", file=sys.stderr)
        sys.exit(1)

    conn_str = os.getenv("PG_CONN", "postgresql+psycopg2://pguser:pgpass@localhost:5432/building_ai")
    n = load_csv(csv_path, conn_str)
    print(f"Inserted {n} rows into sensor_history table")


if __name__ == "__main__":
    _cli() 