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
            "x-csrf-token": self.csrf_token
        }

    def save_or_update(self, payload: dict, timeout=30):
        url = f"{BASE}/saveOrUpdateTerminal/"
        return self.session.put(url, json=payload, headers=self.headers, timeout=timeout)

    def delete_terminals(self, ids: list, timeout=30):
        url = f"{BASE}/deleteTerminals/?fullGws=false"
        return self.session.post(url, json=ids, headers=self.headers, timeout=timeout)
