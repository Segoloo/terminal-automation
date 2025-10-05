import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import pandas as pd
from core.session_manager import SessionManager
from core.tem_automation import TEMAutomation
from core.excel_processor import read_excel
import logging
from datetime import datetime
from PIL import Image, ImageTk
import os

logging.basicConfig(level=logging.INFO)

class ModernApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Automatización TEM - Sebastián Gómez")
        self.root.geometry("1000x720")
        self.root.minsize(950, 680)
        self.root.configure(bg="#F4F6F8")

        # --- Deshabilitar fullscreen ---
        self.root.attributes("-fullscreen", False)
        self.root.resizable(True, True)
        self.root.bind("<F11>", lambda e: None)
        self.root.bind("<Escape>", lambda e: None)

        # --- Variables de estado ---
        self.session_manager = None
        self.tem = None
        self.df = None
        self.df_path = None
        self.remaining_time = 0
        self.timer_running = False

        # --- Estilos ---
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#F4F6F8")
        style.configure("TLabel", background="#F4F6F8", font=("Segoe UI", 11))
        style.configure("Header.TLabel", font=("Segoe UI", 22, "bold"), background="#F4F6F8", foreground="#1F3A93")
        style.configure("TButton", font=("Segoe UI", 11, "bold"), padding=6, foreground="#FFFFFF",
                        background="#1F3A93", borderwidth=0)
        style.map("TButton", background=[("active", "#145A86")])
        style.configure("TLabelframe", background="#F4F6F8", font=("Segoe UI", 12, "bold"))
        style.configure("TLabelframe.Label", background="#F4F6F8", font=("Segoe UI", 13, "bold"))
        style.configure("TProgressbar", thickness=12, troughcolor="#D0D3D4", background="#1F3A93")

        # --- Header ---
        header_frame = ttk.Frame(root)
        header_frame.pack(fill="x", pady=(10,10))

        # Logo más grande y centrado
        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        try:
            logo_image = Image.open(logo_path)
            base_width = 180  # más grande
            w_percent = (base_width / float(logo_image.size[0]))
            h_size = int((float(logo_image.size[1]) * float(w_percent)))
            logo_image = logo_image.resize((base_width, h_size), Image.Resampling.LANCZOS)
            self.logo_image = logo_image
            self.logo_photo = ImageTk.PhotoImage(self.logo_image)
            self.logo_label = ttk.Label(header_frame, image=self.logo_photo, background="#F4F6F8")
            self.logo_label.pack(side="top", pady=5)
        except Exception as e:
            print(f"⚠️ No se pudo cargar el logo: {e}")

        # Título centrado
        header_label = ttk.Label(header_frame, text="⚙️ THE ESTATE MANAGER - AUTOMATIZACIÓN", style="Header.TLabel")
        header_label.pack(side="top", pady=5)

        # --- Contenedor principal ---
        main_frame = ttk.Frame(root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=5)

        # --- Panel superior con dos columnas: Login y Operaciones ---
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="x", expand=False, pady=(0,10))

        # --- Login ---
        self.login_frame = ttk.LabelFrame(top_frame, text="🔑 Inicio de Sesión", padding=15)
        self.login_frame.pack(side="left", fill="both", expand=True, padx=(0,10))

        ttk.Label(self.login_frame, text="Usuario:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.user_entry = ttk.Entry(self.login_frame, width=30)
        self.user_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.login_frame, text="Contraseña:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.pass_entry = ttk.Entry(self.login_frame, show="*", width=30)
        self.pass_entry.grid(row=1, column=1, padx=5, pady=5)

        self.login_btn = ttk.Button(self.login_frame, text="Conectar", command=self.do_login)
        self.login_btn.grid(row=2, column=1, sticky="e", pady=10)

        self.timer_label = ttk.Label(self.login_frame, text="", font=("Segoe UI", 10, "bold"), foreground="#E74C3C")
        self.timer_label.grid(row=2, column=0, sticky="w", padx=5)

        # --- Operaciones ---
        self.proc_frame = ttk.LabelFrame(top_frame, text="📋 Operaciones", padding=15)
        self.proc_frame.pack(side="left", fill="both", expand=True, padx=(10,0))

        self.load_btn = ttk.Button(self.proc_frame, text="📂 Cargar Archivo Excel", command=self.load_excel, state="disabled")
        self.load_btn.pack(anchor="w", padx=5, pady=8)

        self.start_btn = ttk.Button(self.proc_frame, text="▶ Ejecutar Procesamiento", command=self.start_processing, state="disabled")
        self.start_btn.pack(anchor="w", padx=5, pady=8)

        # --- Panel inferior: barra de progreso y logs ---
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill="both", expand=True)

        self.progress = ttk.Progressbar(bottom_frame, mode="determinate", maximum=100)
        self.progress.pack(fill="x", padx=10, pady=(0,5))

        log_frame = ttk.Frame(bottom_frame)
        log_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))

        self.log_box = tk.Text(log_frame, bg="#1E1E1E", fg="#00FF00",
                               font=("Consolas", 12), insertbackground="#00FF00", relief="flat", wrap="word")
        self.log_box.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_box.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_box.config(yscrollcommand=scrollbar.set)

        # --- Footer centrado siempre visible ---
        footer_frame = ttk.Frame(root)
        footer_frame.pack(side="bottom", fill="x", pady=5)
        footer_label = ttk.Label(
            footer_frame,
            text="Desarrollado por Sebastián Gómez López – Aprendiz de Desarrollo de Software – ITM",
            font=("Segoe UI", 10, "bold"),
            background="#F4F6F8",
            foreground="#34495E",
            anchor="center",
            justify="center"
        )
        footer_label.pack(fill="x")

        self.log_msg("💻 Bienvenido. Ingrese sus credenciales y presione 'Conectar'.")

    # --- Logging ---
    def log_msg(self, msg):
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.log_box.insert("end", f"{timestamp} {msg}\n")
        self.log_box.see("end")

    # --- Login ---
    def do_login(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Campos vacíos", "Debe ingresar usuario y contraseña.")
            return

        self.login_btn.config(state="disabled")
        self.log_msg("🔐 Iniciando sesión...")

        def worker():
            sm = SessionManager(debug=False)
            ok, msg = sm.login(username, password)
            if ok:
                self.session_manager = sm
                self.tem = TEMAutomation(sm)
                self.log_msg(f"✅ Sesión iniciada. CSRF: {sm.get_csrf()}")
                self.load_btn.config(state="normal")
                self.start_btn.config(state="normal")
                self.start_timer(900)
            else:
                self.log_msg(f"❌ Error en login: {msg}")
            self.login_btn.config(state="normal")

        threading.Thread(target=worker, daemon=True).start()

    # --- Timer ---
    def start_timer(self, seconds=900):
        self.remaining_time = seconds
        self.timer_running = True
        self.update_timer()

    def update_timer(self):
        if self.timer_running and self.remaining_time > 0:
            mins, secs = divmod(self.remaining_time, 60)
            self.timer_label.config(text=f"Sesión expira en {mins:02d}:{secs:02d}")
            self.remaining_time -= 1
            self.root.after(1000, self.update_timer)
        elif self.remaining_time == 0:
            self.timer_label.config(text="⏰ Sesión expirada")
            self.login_btn.config(state="normal")
            self.load_btn.config(state="disabled")
            self.start_btn.config(state="disabled")
            self.session_manager = None
            self.tem = None
            self.timer_running = False
            self.log_msg("⚠️ La sesión ha expirado, por favor inicie sesión nuevamente.")

    # --- Excel ---
    def load_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Archivos Excel", "*.xlsx;*.xls")])
        if not path:
            return
        try:
            df = read_excel(path)
            self.df = df
            self.df_path = path
            self.log_msg(f"📊 Archivo cargado correctamente ({len(df)} filas).")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # --- Procesamiento ---
    def start_processing(self):
        if self.df is None:
            messagebox.showwarning("Sin archivo", "Debe cargar un Excel antes de procesar.")
            return

        self.start_btn.config(state="disabled")
        self.progress["value"] = 0
        total = len(self.df)
        self.log_msg("🚀 Iniciando procesamiento...")

        def worker():
            for i, row in self.df.iterrows():
                serial = str(row["SERIAL"]).strip()
                codigo = str(row["CODIGO_PUNTO"]).strip() if not pd.isna(row["CODIGO_PUNTO"]) else ""
                try:
                    if not codigo:
                        ok = self.tem.create_terminal(serial)
                        self.log_msg(f"{'✅' if ok else '❌'} Creado: {serial}")
                    else:
                        ok = self.tem.modify_terminal(serial, codigo)
                        self.log_msg(f"{'🟡' if ok else '❌'} Modificado: {serial} → {codigo}")
                except Exception as e:
                    self.log_msg(f"❌ Error con {serial}: {e}")
                # Actualizar barra de progreso en GUI
                self.progress["value"] = ((i + 1) / total) * 100
                self.root.update_idletasks()

            self.log_msg("🎯 Procesamiento finalizado.")
            self.start_btn.config(state="normal")

        # Ejecutar worker en hilo separado para no bloquear la GUI
        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = ModernApp(root)
    root.mainloop()
