"""
alerts_view.py — Vista de alertas: stock bajo, por caducar, caducados
"""

import os
import sys
import customtkinter as ctk

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from views.base_view import BaseView, apply_treeview_style
from config import COLOR_DANGER, COLOR_WARNING, COLOR_INFO, COLOR_CARD_BG


class AlertasView(BaseView):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        apply_treeview_style()
        self._build()
        self.refresh()

    def _build(self):
        hdr = self.make_header(self, "Alertas")
        hdr.pack(fill="x")

        # Botón refrescar
        top_bar = ctk.CTkFrame(self, fg_color="transparent", height=42)
        top_bar.pack(fill="x", padx=10, pady=4)
        top_bar.pack_propagate(False)
        ctk.CTkButton(top_bar, text="↺ Actualizar", command=self.refresh,
                      width=120, height=32).pack(side="left", padx=4)
        self._total_lbl = ctk.CTkLabel(top_bar, text="",
                                        font=ctk.CTkFont(size=12), text_color=COLOR_DANGER)
        self._total_lbl.pack(side="left", padx=16)

        # Scroll container
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=6)

        # Tres secciones
        self._sec_stock = self._make_section(
            scroll, "📦  Stock bajo", "Productos con cantidad ≤ mínimo configurado", COLOR_INFO)
        self._sec_caducar = self._make_section(
            scroll, "⏳  Por caducar (≤ 30 días)", "Productos que caducan pronto", COLOR_WARNING)
        self._sec_caducados = self._make_section(
            scroll, "❌  Caducados", "Productos con fecha de caducidad superada", COLOR_DANGER)

    def _make_section(self, parent, titulo, subtitulo, color):
        """Crea una sección colapsable con tabla de productos."""
        frame = ctk.CTkFrame(parent, fg_color=COLOR_CARD_BG, corner_radius=10)
        frame.pack(fill="x", pady=(0, 12))

        hdr = ctk.CTkFrame(frame, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(10, 2))

        ctk.CTkLabel(hdr, text=titulo,
                     font=ctk.CTkFont(size=14, weight="bold"), text_color=color).pack(side="left")
        badge = ctk.CTkLabel(hdr, text="0", fg_color=color, corner_radius=10,
                              text_color="white", font=ctk.CTkFont(size=11, weight="bold"),
                              width=28, height=20)
        badge.pack(side="left", padx=8)

        ctk.CTkLabel(frame, text=subtitulo,
                     font=ctk.CTkFont(size=11), text_color="#6b7280").pack(
            anchor="w", padx=14, pady=(0, 6))

        # Tabla de productos
        from tkinter import ttk
        tf = ctk.CTkFrame(frame, fg_color="#1c1c1c", corner_radius=6)
        tf.pack(fill="x", padx=14, pady=(0, 12))

        t = ttk.Treeview(
            tf,
            columns=("nombre", "ref", "stock", "minimo", "unidad", "lote", "caducidad", "proveedor"),
            show="headings", style="LabTrack.Treeview", height=4,
        )
        for cid, ctxt, cw in [
            ("nombre",    "Nombre",    200),
            ("ref",       "Ref.",      110),
            ("stock",     "Stock",      80),
            ("minimo",    "Mínimo",     80),
            ("unidad",    "Unidad",     80),
            ("lote",      "Lote",      110),
            ("caducidad", "Caducidad", 100),
            ("proveedor", "Proveedor", 160),
        ]:
            t.heading(cid, text=ctxt)
            t.column(cid, width=cw, anchor="w")

        vsb = ttk.Scrollbar(tf, orient="vertical", command=t.yview,
                            style="LabTrack.Vertical.TScrollbar")
        t.configure(yscrollcommand=vsb.set)
        t.grid(row=0, column=0, sticky="nsew"); vsb.grid(row=0, column=1, sticky="ns")
        tf.grid_rowconfigure(0, weight=1); tf.grid_columnconfigure(0, weight=1)

        return {"frame": frame, "tree": t, "badge": badge}

    def refresh(self):
        from utils.helpers import get_alertas, fmt_fecha_corta, fmt_qty

        try:
            with self.get_session() as s:
                alertas = get_alertas(s)

            self._total_lbl.configure(
                text=f"Total alertas activas: {alertas['total']}" if alertas["total"] > 0
                     else "✔  Sin alertas activas.")

            self._fill_section(self._sec_stock,    alertas["stock_bajo"],  "stock")
            self._fill_section(self._sec_caducar,  alertas["por_caducar"], "caducidad")
            self._fill_section(self._sec_caducados, alertas["caducados"],  "caducidad")

        except Exception as exc:
            self.show_error(str(exc))

    def _fill_section(self, sec, items, modo):
        from utils.helpers import fmt_fecha_corta, fmt_qty

        tree  = sec["tree"]
        badge = sec["badge"]

        for row in tree.get_children():
            tree.delete(row)

        badge.configure(text=str(len(items)))

        for item in items:
            if modo == "stock":
                # item es un Producto
                tree.insert("", "end", values=(
                    item.nombre,
                    item.referencia,
                    fmt_qty(item.cantidad_actual),
                    fmt_qty(item.cantidad_minima),
                    item.unidad or "—",
                    "—",
                    "—",
                    item.proveedor.nombre if item.proveedor else "—",
                ))
            else:
                # item es un LoteProducto
                p = item.producto
                tree.insert("", "end", values=(
                    p.nombre,
                    p.referencia,
                    fmt_qty(item.cantidad),
                    fmt_qty(p.cantidad_minima),
                    p.unidad or "—",
                    item.numero_lote or "—",
                    fmt_fecha_corta(item.fecha_caducidad),
                    p.proveedor.nombre if p.proveedor else "—",
                ))
