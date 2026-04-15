"""
login_view.py — Pantalla de inicio de sesión
"""

import os
import sys
import customtkinter as ctk

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from config import COLOR_ACCENT, COLOR_ACCENT_HOVER

_ICON_PATH = os.path.join(_ROOT, "icon_lab.png")


class LoginView(ctk.CTkFrame):
    """Pantalla de login centrada en la ventana."""

    def __init__(self, parent, on_login_success):
        super().__init__(parent, fg_color="transparent")
        self.on_login_success = on_login_success
        self._build()

    def _build(self):
        # Centrar verticalmente con filas vacías arriba/abajo
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)

        # ── Tarjeta central ──────────────────────────────
        card = ctk.CTkFrame(self, width=400, height=500,
                            fg_color="#1e2329", corner_radius=16)
        card.grid(row=1, column=1)
        card.grid_propagate(False)

        # Icono / logo
        if os.path.isfile(_ICON_PATH):
            try:
                from PIL import Image
                img  = Image.open(_ICON_PATH).resize((72, 72), Image.LANCZOS)
                cimg = ctk.CTkImage(light_image=img, dark_image=img, size=(72, 72))
                lbl  = ctk.CTkLabel(card, image=cimg, text="")
                lbl.pack(pady=(36, 6))
                self._icon_ref = cimg    # evitar GC
            except Exception:
                ctk.CTkLabel(card, text="🔬",
                             font=ctk.CTkFont(size=52)).pack(pady=(36, 6))
        else:
            ctk.CTkLabel(card, text="🔬",
                         font=ctk.CTkFont(size=52)).pack(pady=(36, 6))

        # Título
        ctk.CTkLabel(
            card, text="LabTrack",
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"),
            text_color="white",
        ).pack()

        ctk.CTkLabel(
            card, text="Gestión de Laboratorio",
            font=ctk.CTkFont(size=12),
            text_color="#9ca3af",
        ).pack(pady=(2, 24))

        # Email
        ctk.CTkLabel(card, text="Email", anchor="w",
                     font=ctk.CTkFont(size=12),
                     text_color="#9ca3af").pack(fill="x", padx=44)
        self.email_entry = ctk.CTkEntry(
            card, placeholder_text="admin@labtrack.com",
            height=38, width=312,
        )
        self.email_entry.pack(padx=44, pady=(2, 12))

        # Contraseña
        ctk.CTkLabel(card, text="Contraseña", anchor="w",
                     font=ctk.CTkFont(size=12),
                     text_color="#9ca3af").pack(fill="x", padx=44)
        self.pass_entry = ctk.CTkEntry(
            card, placeholder_text="••••••••",
            show="•", height=38, width=312,
        )
        self.pass_entry.pack(padx=44, pady=(2, 6))

        # Error
        self.error_lbl = ctk.CTkLabel(
            card, text="",
            text_color="#ef4444",
            font=ctk.CTkFont(size=11),
        )
        self.error_lbl.pack()

        # Botón login
        ctk.CTkButton(
            card,
            text="Iniciar sesión",
            height=40, width=312,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._login,
        ).pack(padx=44, pady=(12, 32))

        # Bindings
        self.pass_entry.bind("<Return>",  lambda _: self._login())
        self.email_entry.bind("<Return>", lambda _: self.pass_entry.focus())
        self.email_entry.focus()

    # ── Lógica de autenticación ──────────────────────────

    def _login(self):
        from database import Usuario, get_session

        email    = self.email_entry.get().strip().lower()
        password = self.pass_entry.get()

        if not email or not password:
            self.error_lbl.configure(text="Introduce email y contraseña.")
            return

        try:
            with get_session() as s:
                user = s.query(Usuario).filter(
                    Usuario.email == email,
                    Usuario.activo == True,
                ).first()

                if user and user.check_password(password):
                    # Expunge para usar el objeto fuera de la sesión
                    s.expunge(user)
                    self.on_login_success(user)
                else:
                    self.error_lbl.configure(text="Email o contraseña incorrectos.")
                    self.pass_entry.delete(0, "end")
                    self.pass_entry.focus()

        except Exception as exc:
            self.error_lbl.configure(text=f"Error de conexión: {exc}")
