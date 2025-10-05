# app_beautiful.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import pandas as pd
from core.session_manager import SessionManager
from core.api_client import APIClient
from core.excel_processor import read_excel
from core.worker import process_dataframe
import logging

logging.basicConfig(level=logging.INFO)

class App:
    def __init__(self, root):
        self.root = root
        root.title("Terminal Automation")
        root.geometry("700x500")
        root.configure(bg="#f0f2f5")

        # --- Estilos ---
        style = ttk.Style()
        style.configure("TLabel", background="#f0f2f5", font=("Helvetica", 11))
        style.configure("TButton", font=("Helvetica", 11, "bold"), padding=6)
        style.configure("TEntry", padding=5)
        style.configure("TLabelframe", background="#f0f2f5", font=("Helvetica", 12, "bold"))
        style.configure("TLabelframe.Label", font=("Helvetica", 12, "bold"))

        # --- Login frame ---
        self.login_frame = ttk.LabelFrame(root, text="🔑 Login")
        self.login_frame.pack(fill="x", padx=20, pady=15)

        ttk.Label(self.login_frame, text="Usuario:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.user_entry = ttk.Entry(self.login_frame, width=40)
        self.user_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.login_frame, text="Contraseña:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.pass_entry = ttk.Entry(self.login_frame, show="*", width=40)
        self.pass_entry.grid(row=1, column=1, padx=5, pady=5)

        self.login_btn = ttk.Button(self.login_frame, text="Conectar", command=self.do_login)
        self.login_btn.grid(row=2, column=1, sticky="e", padx=5, pady=10)

        # --- Main operations frame ---
        self.main_frame = ttk.LabelFrame(root, text="⚙ Operaciones")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.load_btn = ttk.Button(self.main_frame, text="📂 Cargar Excel", command=self.load_excel, state="disabled")
        self.load_btn.pack(anchor="w", padx=10, pady=6)

        self.start_btn = ttk.Button(self.main_frame, text="▶ Iniciar Procesamiento", command=self.start_processing, state="disabled")
        self.start_btn.pack(anchor="w", padx=10, pady=6)

        self.log = tk.Text(self.main_frame, height=12, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 10))
        self.log.pack(fill="both", expand=True, padx=10, pady=10)

        # --- State ---
        self.session_manager = None
        self.api_client = None
        self.df = None
        self.df_path = None

    def log_msg(self, msg):
        self.log.insert("end", msg + "\n")
        self.log.see("end")

    def do_login(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Login", "Usuario y contraseña requeridos")
            return

        self.login_btn.config(state="disabled")
        self.log_msg("Iniciando login...")

        def worker():
            try:
                sm = SessionManager()
                ok, msg = sm.login(username, password)
                if not ok:
                    self.log_msg(f"Login falló: {msg}")
                    self.login_btn.config(state="normal")
                    return
                self.session_manager = sm
                self.api_client = APIClient(sm.get_session(), sm.get_csrf())
                self.log_msg(f"Login exitoso. CSRF obtenido: {self.session_manager.get_csrf()}")
                self.load_btn.config(state="normal")
                self.start_btn.config(state="normal")
            except Exception as e:
                self.log_msg(f"Error login: {e}")
                self.login_btn.config(state="normal")

        threading.Thread(target=worker, daemon=True).start()

    def load_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel files","*.xlsx;*.xls")])
        if not path:
            return
        try:
            self.df = read_excel(path)
            self.df_path = path
            self.log_msg(f"Excel cargado: {len(self.df)} filas")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def start_processing(self):
        if self.df is None:
            messagebox.showwarning("Procesar", "Cargue un Excel primero")
            return
        self.start_btn.config(state="disabled")
        self.log_msg("Iniciando procesamiento...")

        def worker_proc():
            try:
                res_df = process_dataframe(self.df.copy(), self.api_client)
                out = self.df_path.replace(".xlsx","_resultados.xlsx")
                res_df.to_excel(out, index=False)
                self.log_msg(f"Procesamiento finalizado. Resultados: {out}")
            except Exception as e:
                self.log_msg(f"Error en procesamiento: {e}")
            finally:
                self.start_btn.config(state="normal")

        threading.Thread(target=worker_proc, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
