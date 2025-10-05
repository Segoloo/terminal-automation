# core/api_client.py
import requests

BASE = "https://estate-manager-nar03.icloud.ingenico.com/emgui/rest/dms/terminals"

class APIClient:
    def __init__(self, session: requests.Session, csrf_token: str):
        self.session = session
        self.csrf_token = csrf_token
        self.headers = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "x-csrf-token": self.csrf_token,
            "x-encode-html-entities": "false"
        }

    def save_or_update(self, payload: dict, timeout=30):
        url = f"{BASE}/saveOrUpdateTerminal/"
        return self.session.put(url, json=payload, headers=self.headers, timeout=timeout)

    def delete_terminals(self, ids: list, timeout=30):
        """Elimina terminales usando el formato que acepta el TEM."""
        url = f"{BASE}/deleteTerminals/?fullGws=false"
        try:
            # algunos entornos requieren lista, otros {"ids": [...]}
            resp = self.session.post(url, json=ids, headers=self.headers, timeout=timeout)
            if not resp.ok:
                # segundo intento con formato alternativo
                alt = self.session.post(url, json={"ids": ids}, headers=self.headers, timeout=timeout)
                return alt
            return resp
        except Exception as e:
            print("Error en delete_terminals:", e)
            raise
