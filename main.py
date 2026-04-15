"""
main.py — LabTrack Desktop
==========================
Punto de entrada de la aplicación de escritorio.
Ejecutar: python main.py
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox

from config import (APP_TITULO, APP_ANCHO, APP_ALTO, APP_MIN_ANCHO, APP_MIN_ALTO,
                    COLOR_SIDEBAR_BG, COLOR_SIDEBAR_HOVER, COLOR_SIDEBAR_ACTIVE,
                    COLOR_ACCENT, COLOR_DANGER, COLOR_WARNING)

# ─── Configuración global CTk ──────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

_ICON_PATH = os.path.join(_HERE, "icon_lab.png")


# ─────────────────────────────────────────────────────────
#  APLICACIÓN PRINCIPAL
# ─────────────────────────────────────────────────────────

class LabTrackApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.current_user   = None
        self._active_view   = None
        self._nav_buttons: dict[str, ctk.CTkButton] = {}

        self.title(APP_TITULO)
        self.geometry(f"{APP_ANCHO}x{APP_ALTO}")
        self.minsize(APP_MIN_ANCHO, APP_MIN_ALTO)
        self._center()
        self.after(100, self._apply_icon)

        # Contenedor raíz único — todo vive aquí
        self._container = ctk.CTkFrame(self, fg_color="transparent")
        self._container.pack(fill="both", expand=True)

        self._show_login()

    # ── Utilidades de ventana ─────────────────────────────

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - APP_ANCHO) // 2
        y = (self.winfo_screenheight() - APP_ALTO)  // 2
        self.geometry(f"+{x}+{y}")

    def _apply_icon(self):
        if not os.path.isfile(_ICON_PATH):
            return
        try:
            import tempfile
            from PIL import Image
            img = Image.open(_ICON_PATH)
            # iconbitmap() requires an .ico file on Windows
            ico_fd, ico_path = tempfile.mkstemp(suffix=".ico")
            os.close(ico_fd)
            img.save(ico_path, format="ICO", sizes=[(32, 32), (48, 48), (64, 64)])
            self._ico_path = ico_path   # keep reference so file isn't deleted
            self.iconbitmap(default=ico_path)
        except Exception:
            pass  # PIL no disponible o icono inválido → sin icono

    # ─────────────────────────────────────────────────────
    #  PANTALLA DE LOGIN
    # ─────────────────────────────────────────────────────

    def _show_login(self):
        self._clear_root()
        from views.login_view import LoginView
        LoginView(self._container, on_login_success=self._on_login).pack(
            fill="both", expand=True)

    def _on_login(self, user):
        self.current_user = user
        self._show_main()

    # ─────────────────────────────────────────────────────
    #  PANTALLA PRINCIPAL  (sidebar + contenido)
    # ─────────────────────────────────────────────────────

    def _show_main(self):
        self._clear_root()
        self._active_view  = None
        self._nav_buttons  = {}

        # Sidebar izquierdo — ancho fijo, altura completa
        self._sidebar = ctk.CTkFrame(
            self._container, width=220, fg_color=COLOR_SIDEBAR_BG, corner_radius=0)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)   # mantiene 220 px de ancho

        # Área de contenido — ocupa todo lo restante
        self._content = ctk.CTkFrame(
            self._container, fg_color="#0d1117", corner_radius=0)
        self._content.pack(side="left", fill="both", expand=True)

        self._build_sidebar()
        self._navigate("dashboard")

    # ─────────────────────────────────────────────────────
    #  SIDEBAR
    # ─────────────────────────────────────────────────────

    def _build_sidebar(self):
        sb = self._sidebar

        # ── Logo ────────────────────────────────────────
        logo_row = ctk.CTkFrame(sb, fg_color="transparent", height=72)
        logo_row.pack(fill="x")
        logo_row.pack_propagate(False)

        if os.path.isfile(_ICON_PATH):
            try:
                from PIL import Image
                img = Image.open(_ICON_PATH).resize((36, 36), Image.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(36, 36))
                ctk.CTkLabel(logo_row, image=ctk_img, text="",
                             width=36).pack(side="left", padx=(14, 6), pady=18)
                self._logo_img_ref = ctk_img  # evitar GC
            except Exception:
                ctk.CTkLabel(logo_row, text="🔬",
                             font=ctk.CTkFont(size=28)).pack(side="left", padx=(14, 6), pady=18)
        else:
            ctk.CTkLabel(logo_row, text="🔬",
                         font=ctk.CTkFont(size=28)).pack(side="left", padx=(14, 6), pady=18)

        ctk.CTkLabel(
            logo_row, text="LabTrack",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="white",
        ).pack(side="left", pady=18)

        ctk.CTkFrame(sb, height=1, fg_color="#2d333b").pack(fill="x", padx=12)

        # ── Info usuario ─────────────────────────────────
        nombre = self.current_user.nombre if self.current_user else "—"
        rol    = self.current_user.rol    if self.current_user else ""
        ctk.CTkLabel(sb, text=nombre,
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="white", anchor="w").pack(
            fill="x", padx=16, pady=(10, 0))
        ctk.CTkLabel(sb,
                     text="Administrador" if rol == "admin" else "Usuario",
                     font=ctk.CTkFont(size=10), text_color=COLOR_ACCENT, anchor="w").pack(
            fill="x", padx=16)

        ctk.CTkFrame(sb, height=1, fg_color="#2d333b").pack(fill="x", padx=12, pady=8)

        # ── Botones de navegación ─────────────────────────
        nav_items = [
            ("dashboard",   "  📊  Dashboard"),
            ("productos",   "  📦  Productos"),
            ("proveedores", "  🏭  Proveedores"),
            ("pedidos",     "  📋  Pedidos"),
            ("recepciones", "  📥  Recepciones"),
            ("movimientos", "  🔄  Movimientos"),
            ("alertas",     "  ⚠   Alertas"),
        ]
        if self.current_user and self.current_user.es_admin:
            nav_items.append(("admin", "  ⚙   Admin"))

        for key, label in nav_items:
            btn = ctk.CTkButton(
                sb,
                text=label,
                anchor="w",
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                hover_color=COLOR_SIDEBAR_HOVER,
                text_color="white",
                height=38,
                corner_radius=6,
                command=lambda k=key: self._navigate(k),
            )
            btn.pack(fill="x", padx=8, pady=2)
            self._nav_buttons[key] = btn

        # ── Espacio flexible → empuja logout al fondo ─────
        ctk.CTkFrame(sb, fg_color="transparent").pack(fill="both", expand=True)

        ctk.CTkFrame(sb, height=1, fg_color="#2d333b").pack(fill="x", padx=12, pady=4)
        ctk.CTkButton(
            sb,
            text="  🚪  Cerrar sesión",
            anchor="w",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color="#7f1d1d",
            text_color="#9ca3af",
            height=36,
            corner_radius=6,
            command=self._logout,
        ).pack(fill="x", padx=8, pady=(0, 12))

    # ─────────────────────────────────────────────────────
    #  NAVEGACIÓN
    # ─────────────────────────────────────────────────────

    def _navigate(self, key: str):
        # Resaltar botón activo
        for k, btn in self._nav_buttons.items():
            active = (k == key)
            btn.configure(
                fg_color=COLOR_SIDEBAR_ACTIVE if active else "transparent",
                font=ctk.CTkFont(size=13, weight="bold" if active else "normal"),
            )

        # Destruir vista anterior
        if self._active_view is not None:
            self._active_view.destroy()
            self._active_view = None

        # Crear y empaquetar nueva vista
        view = self._create_view(key)
        if view is not None:
            view.pack(fill="both", expand=True)
            self._active_view = view

        # Actualizar badge de alertas en el botón
        self.after(300, self._update_alert_badge)

    def _create_view(self, key: str):
        try:
            if key == "dashboard":
                from views.dashboard_view import DashboardView
                return DashboardView(self._content, self)

            if key == "productos":
                from views.products_view import ProductosView
                return ProductosView(self._content, self)

            if key == "proveedores":
                from views.suppliers_view import ProveedoresView
                return ProveedoresView(self._content, self)

            if key == "pedidos":
                from views.orders_view import PedidosView
                return PedidosView(self._content, self)

            if key == "recepciones":
                from views.receptions_view import RecepcionesView
                return RecepcionesView(self._content, self)

            if key == "movimientos":
                from views.movements_view import MovimientosView
                return MovimientosView(self._content, self)

            if key == "alertas":
                from views.alerts_view import AlertasView
                return AlertasView(self._content, self)

            if key == "admin" and self.current_user and self.current_user.es_admin:
                from views.admin_view import AdminView
                return AdminView(self._content, self)

        except Exception as exc:
            import traceback
            traceback.print_exc()
            frame = ctk.CTkFrame(self._content, fg_color="transparent")
            ctk.CTkLabel(
                frame,
                text=f"Error al cargar la vista '{key}':\n\n{exc}",
                text_color=COLOR_DANGER,
                font=ctk.CTkFont(size=13),
                justify="left",
            ).pack(expand=True, padx=40)
            return frame

        return None

    def _update_alert_badge(self):
        """Actualiza el contador de alertas en el botón del sidebar."""
        try:
            from utils.helpers import get_alertas
            from database import get_session
            with get_session() as s:
                n = get_alertas(s)["total"]
            btn = self._nav_buttons.get("alertas")
            if btn:
                text  = f"  ⚠   Alertas  ({n})" if n > 0 else "  ⚠   Alertas"
                color = COLOR_WARNING if n > 0 else "white"
                btn.configure(text=text, text_color=color)
        except Exception:
            pass

    # ─────────────────────────────────────────────────────
    #  LOGOUT
    # ─────────────────────────────────────────────────────

    def _logout(self):
        self.current_user  = None
        self._active_view  = None
        self._nav_buttons  = {}
        self._show_login()

    # ─────────────────────────────────────────────────────
    #  HELPERS
    # ─────────────────────────────────────────────────────

    def _clear_root(self):
        """Destruye todos los hijos del frame raíz."""
        for w in self._container.winfo_children():
            w.destroy()


# ─────────────────────────────────────────────────────────
#  PUNTO DE ENTRADA
# ─────────────────────────────────────────────────────────

def main():
    try:
        from database import init_db
        init_db()
    except Exception as exc:
        import traceback
        traceback.print_exc()
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Error de Base de Datos",
            f"No se pudo inicializar la base de datos:\n\n{exc}\n\n"
            f"Comprueba la ruta en config.py\n"
            f"Ruta actual: {__import__('config').DATABASE_PATH}",
        )
        root.destroy()
        sys.exit(1)

    app = LabTrackApp()
    app.mainloop()


if __name__ == "__main__":
    main()
