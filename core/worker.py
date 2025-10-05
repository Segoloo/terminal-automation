import time
import logging
from .excel_processor import row_to_payload

logger = logging.getLogger(__name__)

def clean_codigo_punto(value):
    """
    Limpia y formatea el código de punto:
    - Convierte floats (ej. 1234.0 → "1234")
    - Maneja valores vacíos, nulos o 'nan'
    """
    if value is None:
        return ""
    try:
        if isinstance(value, float):
            if value.is_integer():
                return str(int(value))
            return str(value)
        value_str = str(value).strip()
        if value_str.lower() in ("nan", "none", ""):
            return ""
        if value_str.endswith(".0"):
            # Si viene de Excel como texto tipo "1234.0"
            value_str = value_str[:-2]
        return value_str
    except Exception:
        return str(value)


def process_dataframe(df, api_client, delay=0.3, max_retries=3):
    results = []

    for idx, raw_row in df.iterrows():
        row = raw_row.to_dict()
        action = str(row.get("action", "")).strip().lower()

        # 🔧 Normalizar campos importantes
        serial = str(row.get("SERIAL") or row.get("serial") or "").strip()
        codigo_raw = row.get("CODIGO_PUNTO") or row.get("codigo_punto") or row.get("Codigo_Punto")
        codigo_punto = clean_codigo_punto(codigo_raw)

        try:
            if action == "delete" or str(row.get("delete", "")).strip().lower() == "yes":
                # 🔥 Acción: Eliminar terminal
                term_id = row.get("id")
                if not term_id:
                    results.append({
                        "row": idx + 2,
                        "status": "SKIP_NO_ID",
                        "response": "No ID para eliminar"
                    })
                    continue

                resp = api_client.delete_terminals([term_id])
                results.append({
                    "row": idx + 2,
                    "status": "OK" if resp.ok else "ERROR",
                    "code": resp.status_code,
                    "response": resp.text
                })

            else:
                # 🔥 Acción: Crear o actualizar terminal
                payload = row_to_payload({
                    **row,
                    "SERIAL": serial,
                    "CODIGO_PUNTO": codigo_punto
                })

                attempt = 0
                resp = None

                while attempt < max_retries:
                    resp = api_client.save_or_update(payload)
                    if resp.ok:
                        break
                    attempt += 1
                    time.sleep(2 ** attempt)

                results.append({
                    "row": idx + 2,
                    "status": "OK" if resp and resp.ok else "ERROR",
                    "code": resp.status_code if resp else None,
                    "response": resp.text if resp else "No response"
                })

        except Exception as e:
            logger.exception("Error procesando fila")
            results.append({
                "row": idx + 2,
                "status": "EXCEPTION",
                "response": str(e)
            })

        time.sleep(delay)

    # 🧾 Guardar resultados en el DataFrame
    df["Result"] = [r["status"] for r in results]
    df["API_Response"] = [r["response"] for r in results]
    return df
