# core/worker.py
import time
import logging
from .excel_processor import row_to_payload

logger = logging.getLogger(__name__)

def process_dataframe(df, api_client, delay=0.3, max_retries=3):
    results = []
    for idx, raw_row in df.iterrows():
        row = raw_row.to_dict()
        # Decide acción: si columna "action" == "delete" o si id tiene valor para delete
        action = row.get("action", "").strip().lower()
        try:
            if action == "delete" or (row.get("delete","").strip().lower()=="yes"):
                # Necesita tener id en la fila
                ids = [row["id"]] if row["id"] else []
                if not ids or ids==[""]:
                    results.append({"row": idx+2, "status": "SKIP_NO_ID", "response": "No ID para eliminar"})
                else:
                    resp = api_client.delete_terminals(ids)
                    results.append({"row": idx+2, "status": "OK" if resp.ok else "ERROR", "code": resp.status_code, "response": resp.text})
            else:
                payload = row_to_payload(row)
                attempt = 0
                resp = None
                while attempt < max_retries:
                    resp = api_client.save_or_update(payload)
                    if resp.ok:
                        break
                    attempt += 1
                    time.sleep(2 ** attempt)
                results.append({"row": idx+2, "status": "OK" if resp and resp.ok else "ERROR", "code": resp.status_code if resp else None, "response": resp.text if resp else "No response"})
        except Exception as e:
            logger.exception("Error procesando fila")
            results.append({"row": idx+2, "status": "EXCEPTION", "response": str(e)})
        time.sleep(delay)

    # Añadir resultados a df y guardar
    df["Result"] = [r["status"] for r in results]
    df["API_Response"] = [r["response"] for r in results]
    return df
