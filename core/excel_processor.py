# core/excel_processor.py
import pandas as pd

def read_excel(path: str):
    """Lee un archivo Excel con las columnas SERIAL y CODIGO_PUNTO."""
    df = pd.read_excel(path)
    df.columns = [c.strip().upper() for c in df.columns]
    required = {"SERIAL", "CODIGO_PUNTO"}
    if not required.issubset(df.columns):
        raise ValueError(f"El Excel debe tener las columnas: {required}")
    return df
