# core/tem_automation.py
import json
import requests
from datetime import datetime
import os

LOG_PATH = os.path.join("logs", "automation_log.txt")


class TEMAutomation:
    def __init__(self, session_manager):
        self.session = session_manager.get_session()
        self.csrf = session_manager.get_csrf()
        self.headers = session_manager.auth_headers()

        # Crear carpeta logs si no existe
        os.makedirs("logs", exist_ok=True)

    # ==========================================================
    # 🧾 LOGGING
    # ==========================================================
    def _log_action(self, action, serial, status, detail=""):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {action.upper()} | {serial} | {status} | {detail}\n")

    # ==========================================================
    # 🔍 VERIFICAR SI EL TERMINAL EXISTE (versión robusta)
    # ==========================================================
    def terminal_exists(self, serial: str):
        """
        Busca un terminal en la carpeta 'Migración' por su signature (más confiable).
        """
        try:
            url = (
                "https://estate-manager-nar03.icloud.ingenico.com/"
                "emgui/rest/dms/terminals/terminalLights/?full=false&length=100&start=0"
            )
            payload = {
                "sortColumns": [{"key": {"header": "NAME"}, "value": True}],
                "criteriaAndList": [
                    {"key": {"header": "SIGNATURE"}, "value": serial},
                    {"key": {"header": "PARENT_ID"}, "value": "2a2c6a55:19875777b4c:-3daa:AC1A2373"},
                    {"key": {"header": "CATEGORY"}, "value": 1}
                ],
                "criteriaOrLists": [],
                "geoLocationSearch": None,
                "displayedColumns": [
                    {"header": "NAME"},
                    {"header": "SIGNATURE"},
                    {"header": "TYPE"}
                ]
            }

            resp = self.session.post(url, headers=self.headers, json=payload)
            if not resp.ok:
                self._log_action("CHECK_EXIST", serial, "FAIL", f"HTTP {resp.status_code}")
                return None

            data = resp.json()
            items = data.get("data") if isinstance(data, dict) else data
            if not items:
                self._log_action("CHECK_EXIST", serial, "NOT_FOUND", "No existe en Migración")
                return None

            for item in items:
                sig = item.get("signature") or item.get("SIGNATURE")
                if sig and sig.strip().upper() == serial.strip().upper():
                    term_id = item.get("id") or item.get("ID")
                    self._log_action("CHECK_EXIST", serial, "FOUND", f"ID {term_id}")
                    return term_id

            self._log_action("CHECK_EXIST", serial, "NOT_FOUND", "No coincide signature exacto")
            return None

        except Exception as e:
            self._log_action("CHECK_EXIST", serial, "ERROR", str(e))
            return None


    # ==========================================================
    # 💾 CREAR O ACTUALIZAR TERMINAL
    # ==========================================================
    def create_or_update_terminal(self, serial: str, codigo_punto: str = None) -> bool:
        """
        Si el terminal existe, lo actualiza (mantiene el mismo ID).
        Si no, lo crea.
        """
        try:
            existing_id = self.terminal_exists(serial)

            # Validar firma (siempre antes de PUT)
            self.session.get(
                f"https://estate-manager-nar03.icloud.ingenico.com/"
                f"emgui/rest/dms/terminals/validateTerminalSignature/?signature={serial}",
                headers=self.headers
            )

            payload = {
                "terminalAndGeolocation": {
                    "id": existing_id if existing_id else None,
                    "signature": serial,
                    "name": codigo_punto if codigo_punto else serial,
                    "description": "",
                    "status": 0,
                    "type": "AXIUMNX",
                    "category": 1,
                    "parentId": "2a2c6a55:19875777b4c:-3daa:AC1A2373",  # Carpeta Migración
                    "merchantId": None,
                    "geoLocation": None,
                    "customValues": {},
                    "automaticSwap": False
                },
                "tagIds": None,
                "callSchedule": None,
                "blockData": None,
                "attachData": None,
                "ipRange": None,
                "wipeRequest": False
            }

            url = (
                "https://estate-manager-nar03.icloud.ingenico.com/"
                "emgui/rest/dms/terminals/saveOrUpdateTerminal/"
            )
            resp = self.session.put(url, headers=self.headers, json=payload)
            ok = resp.status_code == 200

            action = "UPDATE" if existing_id else "CREATE"
            self._log_action(action, serial, "OK" if ok else f"FAIL | HTTP {resp.status_code}", resp.text[:120])
            return ok

        except Exception as e:
            self._log_action("CREATE_OR_UPDATE", serial, "ERROR", str(e))
            return False

    # ==========================================================
    # 🧩 COMPATIBILIDAD CON CÓDIGO ANTIGUO
    # ==========================================================
    def create_terminal(self, serial: str, codigo_punto: str = None) -> bool:
        """Compatibilidad con versiones previas del código."""
        return self.create_or_update_terminal(serial, codigo_punto)

    def modify_terminal(self, serial: str, codigo_punto: str) -> bool:
        """Compatibilidad con versiones previas del código."""
        return self.create_or_update_terminal(serial, codigo_punto)
