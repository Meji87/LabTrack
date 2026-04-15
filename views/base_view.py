"""
base_view.py — Clase base y utilidades compartidas para todas las vistas
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from config import (COLOR_ACCENT, COLOR_ACCENT_HOVER, COLOR_HEADER_BG,
                    COLOR_CARD_BG, COLOR_SIDEBAR_ACTIVE)


# ─────────────────────────────────────────────────────────
#  ESTILOS TTK (Treeview oscuro)
# ─────────────────────────────────────────────────────────

def apply_treeview_style():
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure(
        "LabTrack.Treeview",
        background="#1c1c1c",
        foreground="#e0e0e0",
        fieldbackground="#1c1c1c",
        borderwidth=0,
        rowheight=30,
        font=("Segoe UI", 12),
    )
    style.configure(
        "LabTrack.Treeview.Heading",
        background="#111827",
        foreground="#9ca3af",
        borderwidth=0,
        relief="flat",
        font=("Segoe UI", 12, "bold"),
    )
    style.map(
        "LabTrack.Treeview",
        background=[("selected", "#0d5c3d")],
        foreground=[("selected", "white")],
    )
    style.configure(
        "LabTrack.Vertical.TScrollbar",
        background="#2d2d2d",
        troughcolor="#1c1c1c",
        arrowcolor="#9ca3af",
        borderwidth=0,
        width=10,
    )
    style.configure(
        "LabTrack.Horizontal.TScrollbar",
        background="#2d2d2d",
        troughcolor="#1c1c1c",
        arrowcolor="#9ca3af",
        borderwidth=0,
        width=10,
    )


# ─────────────────────────────────────────────────────────
#  BASE VIEW
# ─────────────────────────────────────────────────────────

class BaseView(ctk.CTkFrame):
    """Clase base para todas las vistas de LabTrack."""

    def __init__(self, parent, app, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(parent, **kwargs)
        self.app = app

    # ── Accesos rápidos ──────────────────────────────────

    @property
    def current_user(self):
        return self.app.current_user

    def get_session(self):
        from database import get_session
        return get_session()

    # ── Diálogos ─────────────────────────────────────────

    def show_error(self, msg: str, title: str = "Error"):
        messagebox.showerror(title, msg, parent=self.winfo_toplevel())

    def show_info(self, msg: str, title: str = "Información"):
        messagebox.showinfo(title, msg, parent=self.winfo_toplevel())

    def confirm(self, msg: str, title: str = "Confirmar") -> bool:
        return messagebox.askyesno(title, msg, parent=self.winfo_toplevel())

    # ── Widgets reutilizables ─────────────────────────────

    def make_header(self, parent,
                    titulo: str,
                    btn_label: str = None,
                    btn_cmd=None,
                    solo_admin: bool = False) -> ctk.CTkFrame:
        """Barra de cabecera con título y botón opcional."""
        hdr = ctk.CTkFrame(parent, height=58, fg_color=COLOR_HEADER_BG, corner_radius=0)

        ctk.CTkLabel(
            hdr, text=titulo,
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="white",
        ).pack(side="left", padx=20, pady=10)

        if btn_label and btn_cmd:
            show = (not solo_admin) or (self.current_user and self.current_user.es_admin)
            if show:
                ctk.CTkButton(
                    hdr, text=btn_label, command=btn_cmd,
                    fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
                    height=34, font=ctk.CTkFont(size=12),
                ).pack(side="right", padx=16, pady=12)

        return hdr

    def make_table(self, parent, cols: list[tuple]) -> tuple:
        """
        Crea frame + Treeview estilizado.

        cols: [(id, encabezado, ancho_px, alineacion='w'), ...]
        Returns: (frame, treeview)
        """
        frame = ctk.CTkFrame(parent, fg_color="#1c1c1c", corner_radius=8)

        col_ids = [c[0] for c in cols]
        tree = ttk.Treeview(
            frame, columns=col_ids, show="headings",
            style="LabTrack.Treeview", selectmode="browse",
        )

        for col in cols:
            cid, ctxt, cw = col[0], col[1], col[2]
            anchor = col[3] if len(col) > 3 else "w"
            tree.heading(cid, text=ctxt, anchor=anchor)
            tree.column(cid, width=cw, minwidth=30, anchor=anchor, stretch=True)

        vsb = ttk.Scrollbar(frame, orient="vertical",   command=tree.yview,
                            style="LabTrack.Vertical.TScrollbar")
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview,
                            style="LabTrack.Horizontal.TScrollbar")
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        return frame, tree

    def refresh(self):
        """Recargar datos. Sobreescribir en subclases."""
        pass


# ─────────────────────────────────────────────────────────
#  MODAL BASE
# ─────────────────────────────────────────────────────────

class ModalBase(ctk.CTkToplevel):
    """Ventana modal reutilizable para formularios."""

    def __init__(self, parent, titulo: str, ancho: int = 520, alto: int = 480):
        super().__init__(parent)
        self.title(titulo)
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()

        # Centrar en pantalla
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = (sw - ancho) // 2
        y  = (sh - alto)  // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

        # Cabecera
        hdr = ctk.CTkFrame(self, height=46, fg_color="#111827", corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr, text=titulo,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="white",
        ).pack(side="left", padx=16, pady=8)

        # Área de contenido con scroll
        self.content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=16, pady=8)
        self.content.grid_columnconfigure(1, weight=1)

        # Barra de botones
        self.btn_bar = ctk.CTkFrame(self, height=52, fg_color="transparent")
        self.btn_bar.pack(fill="x", padx=16, pady=(0, 12))
        self.btn_bar.pack_propagate(False)

        self.after(200, self._set_icon)

    def _set_icon(self):
        import os
        _ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ico_path = os.path.join(_ROOT, "icon_lab.png")
        # busca el .ico que main.py ya generó en temp
        app = self.master
        while app and not hasattr(app, '_ico_path'):
            app = getattr(app, 'master', None)
        if app and hasattr(app, '_ico_path') and os.path.isfile(app._ico_path):
            try:
                self.iconbitmap(app._ico_path)
            except Exception:
                pass

    # ── helpers de formulario ─────────────────────────────

    def add_label(self, text: str, row: int):
        lbl = ctk.CTkLabel(
            self.content, text=text,
            font=ctk.CTkFont(size=12), text_color="#9ca3af", anchor="w",
        )
        lbl.grid(row=row, column=0, columnspan=2, sticky="w", padx=4, pady=(8, 2))
        return lbl

    def add_entry(self, row: int, placeholder: str = "", **kw) -> ctk.CTkEntry:
        e = ctk.CTkEntry(self.content, placeholder_text=placeholder, **kw)
        e.grid(row=row, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 4))
        return e

    def add_combo(self, row: int, values: list, **kw) -> ctk.CTkComboBox:
        cb = ctk.CTkComboBox(self.content, values=values, state="readonly", **kw)
        cb.grid(row=row, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 4))
        return cb

    def add_textbox(self, row: int, height: int = 70, **kw) -> ctk.CTkTextbox:
        tb = ctk.CTkTextbox(self.content, height=height, **kw)
        tb.grid(row=row, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 4))
        return tb

    def add_buttons(self, on_save, on_cancel=None):
        if on_cancel is None:
            on_cancel = self.destroy
        ctk.CTkButton(
            self.btn_bar, text="Cancelar", width=100,
            fg_color="#374151", hover_color="#4b5563",
            command=on_cancel,
        ).pack(side="right", padx=4)
        ctk.CTkButton(
            self.btn_bar, text="Guardar", width=120,
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
            command=on_save,
        ).pack(side="right", padx=4)

    def get_tb(self, textbox: ctk.CTkTextbox) -> str:
        return textbox.get("1.0", "end").strip()

    def set_tb(self, textbox: ctk.CTkTextbox, text: str):
        textbox.delete("1.0", "end")
        if text:
            textbox.insert("1.0", text)
