MOCK = {
    "HVAC-01": {"temperature": 72, "vibration": 0.21, "pressure": 12.3},
    "CHILLER-02": {"temperature": 45, "vibration": 0.15, "pressure": 22.0},
}

def fetch_live_data(equipment_id: str) -> dict:
    return MOCK.get(equipment_id, {}) 