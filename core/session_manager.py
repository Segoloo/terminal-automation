# core/session_manager.py
from playwright.sync_api import sync_playwright
import requests

BASE = "https://estate-manager-nar03.icloud.ingenico.com"
LOGIN_URL = f"{BASE}/emgui/"
CONTEXT_URL = f"{BASE}/emgui/rest/home/context"

class SessionManager:
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.session = requests.Session()
        self.csrf_token = None

    def login(self, username: str, password: str) -> (bool, str):
        """
        Inicia sesión con Playwright (headless), obtiene cookies + csrf.
        """
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)  # headless = sin abrir ventana
                page = browser.new_page()

                if self.debug:
                    print("[*] Abriendo login:", LOGIN_URL)

                # 1. Ir al login
                page.goto(LOGIN_URL)

                # 2. Completar usuario y contraseña (ajusta los selectores según tu HTML)
                page.fill('input[name="username"]', username)
                page.fill('input[name="password"]', password)

                # 3. Enviar formulario (Enter o click en el botón)
                page.keyboard.press("Enter")
                page.wait_for_load_state("networkidle")

                # 4. Exportar cookies del navegador
                cookies = page.context.cookies()
                browser.close()

            if self.debug:
                print("[*] Cookies Playwright:", cookies)

            # Pasar cookies a requests.Session
            for c in cookies:
                self.session.cookies.set(c["name"], c["value"], domain=c.get("domain"))

            # 5. Pedir context para obtener el token real
            ctx = self.session.get(CONTEXT_URL, headers={"x-csrf-request": "true"})
            ctx.raise_for_status()
            self.csrf_token = ctx.headers.get("x-csrf-token")

            if not self.csrf_token:
                return False, "Login OK pero no se encontró x-csrf-token"

            return True, "Login OK"
        except Exception as e:
            return False, f"Error en login con Playwright: {e}"

    def get_session(self):
        return self.session

    def get_csrf(self):
        return self.csrf_token

    def auth_headers(self):
        """Headers listos para API"""
        return {
            "x-csrf-token": self.csrf_token,
            "Content-Type": "application/json"
        }


if __name__ == "__main__":
    sm = SessionManager(debug=True)
    ok, msg = sm.login("user", "pass")
    print("Login exitoso:", ok)
    print("Mensaje:", msg)
    print("CSRF token:", sm.get_csrf())

