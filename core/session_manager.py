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
        Inicia sesión headless en el TEM, copia las cookies al requests.Session
        y obtiene el token CSRF necesario para las peticiones REST.
        """
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                if self.debug:
                    print("[*] Abriendo login:", LOGIN_URL)
                page.goto(LOGIN_URL)

                # Ingreso de credenciales
                page.fill('input[name="username"]', username)
                page.fill('input[name="password"]', password)
                page.keyboard.press("Enter")
                page.wait_for_load_state("networkidle")

                # Guardar cookies
                cookies = page.context.cookies()
                browser.close()

            # Transferir cookies a requests
            for c in cookies:
                self.session.cookies.set(c["name"], c["value"], domain=c.get("domain"))

            # Solicitar el contexto para obtener el token CSRF
            ctx = self.session.get(CONTEXT_URL, headers={"x-csrf-request": "true"})
            ctx.raise_for_status()
            self.csrf_token = ctx.headers.get("x-csrf-token")

            if not self.csrf_token:
                return False, "Login OK, pero no se encontró token CSRF"
            return True, "Login OK"

        except Exception as e:
            return False, f"Error en login con Playwright: {e}"

    def get_session(self):
        return self.session

    def get_csrf(self):
        return self.csrf_token

    def auth_headers(self):
        return {
            "x-csrf-token": self.csrf_token,
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*"
        }
