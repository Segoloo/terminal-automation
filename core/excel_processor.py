# core/excel_processor.py
import pandas as pd

REQUIRED_COLS = ["id", "signature", "name", "type", "parentId"]

def read_excel(path: str):
    df = pd.read_excel(path, dtype=str).fillna("")
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas en Excel: {missing}")
    return df

def row_to_payload(row: dict) -> dict:
    return {
        "terminalAndGeolocation": {
            "id": row["id"] if row["id"] != "" else None,
            "signature": row["signature"],
            "name": row["name"],
            "description": None,
            "status": 0,
            "type": row["type"],
            "category": 1,
            "parentId": row["parentId"],
            "merchantId": None,
            "geoLocation": None,
            "customValues": {},
            "automaticSwap": False
        },
        "tagIds": None,
        "callSchedule": {
            "callSchedulingEnabled": False,
            "forceDate": None,
            "frequency": 28,
            "retryPeriod": 24,
            "timezoneAdjustment": 0,
            "loadBalanceEnabled": False,
            "startHour": "00",
            "startMinute": "00",
            "endHour": "00",
            "endMinute": "00",
            "rejectIfOutwithWindow": False,
            "disableParentUpdate": False
        },
        "blockData": None,
        "attachData": None,
        "ipRange": None
    }
