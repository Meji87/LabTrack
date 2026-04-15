"""
dashboard_view.py — Panel principal con KPIs, alertas y últimos movimientos
"""

import os
import sys
import customtkinter as ctk
from tkinter import ttk

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from views.base_view import BaseView, apply_treeview_style
from config import (COLOR_ACCENT, COLOR_DANGER, COLOR_WARNING,
                    COLOR_SUCCESS, COLOR_INFO, COLOR_HEADER_BG, COLOR_CARD_BG)


class DashboardView(BaseView):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        apply_treeview_style()
        self._build()
        self.refresh()

    # ─────────────────────────────────────────────────────
    #  CONSTRUCCIÓN DE UI
    # ─────────────────────────────────────────────────────

    def _build(self):
        # Cabecera
        hdr = self.make_header(self, "Dashboard")
        hdr.pack(fill="x")

        # Scroll principal
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=10)

        # --- Fila de tarjetas KPI ---
        kpi_row = ctk.CTkFrame(scroll, fg_color="transparent")
        kpi_row.pack(fill="x", pady=(0, 16))
        for i in range(4):
            kpi_row.grid_columnconfigure(i, weight=1)

        self.kpi_productos  = self._kpi_card(kpi_row, "Productos activos",  "0", COLOR_INFO,    0)
        self.kpi_pedidos    = self._kpi_card(kpi_row, "Pedidos pendientes", "0", COLOR_WARNING,  1)
        self.kpi_alertas    = self._kpi_card(kpi_row, "Alertas activas",    "0", COLOR_DANGER,   2)
        self.kpi_mov        = self._kpi_card(kpi_row, "Movimientos hoy",    "0", COLOR_ACCENT,   3)

        # --- Alertas ---
        alertas_frame = ctk.CTkFrame(scroll, fg_color=COLOR_CARD_BG, corner_radius=10)
        alertas_frame.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            alertas_frame, text="⚠  Alertas",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_WARNING,
        ).pack(anchor="w", padx=16, pady=(12, 6))

        self.alertas_inner = ctk.CTkFrame(alertas_frame, fg_color="transparent")
        self.alertas_inner.pack(fill="x", padx=16, pady=(0, 12))

        # --- Dos columnas: movimientos recientes + productos críticos ---
        cols = ctk.CTkFrame(scroll, fg_color="transparent")
        cols.pack(fill="both", expand=True)
        cols.grid_columnconfigure(0, weight=3)
        cols.grid_columnconfigure(1, weight=2)

        # Últimos movimientos
        left = ctk.CTkFrame(cols, fg_color=COLOR_CARD_BG, corner_radius=10)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(
            left, text="Últimos movimientos",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="white",
        ).pack(anchor="w", padx=14, pady=(12, 6))

        self.mov_frame, self.mov_tree = self.make_table(left, [
            ("fecha",     "Fecha",     120),
            ("tipo",      "Tipo",       80),
            ("producto",  "Producto",  200),
            ("cantidad",  "Cantidad",   80, "e"),
            ("usuario",   "Usuario",    100),
        ])
        self.mov_frame.pack(fill="both", expand=True, padx=8, pady=(0, 10))

        # Productos críticos
        right = ctk.CTkFrame(cols, fg_color=COLOR_CARD_BG, corner_radius=10)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        ctk.CTkLabel(
            right, text="Productos críticos",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="white",
        ).pack(anchor="w", padx=14, pady=(12, 6))

        self.crit_frame, self.crit_tree = self.make_table(right, [
            ("nombre",  "Nombre",   160),
            ("stock",   "Stock",     70, "e"),
            ("minimo",  "Mínimo",    70, "e"),
        ])
        self.crit_frame.pack(fill="both", expand=True, padx=8, pady=(0, 10))

    def _kpi_card(self, parent, titulo, valor, color, col):
        card = ctk.CTkFrame(parent, fg_color=COLOR_CARD_BG, corner_radius=10, height=90)
        card.grid(row=0, column=col, padx=6, pady=4, sticky="ew")
        card.grid_propagate(False)

        ctk.CTkLabel(
            card, text=titulo,
            font=ctk.CTkFont(size=11), text_color="#9ca3af",
        ).place(x=14, y=12)

        lbl = ctk.CTkLabel(
            card, text=valor,
            font=ctk.CTkFont(size=30, weight="bold"), text_color=color,
        )
        lbl.place(x=14, y=34)
        return lbl

    # ─────────────────────────────────────────────────────
    #  REFRESCO DE DATOS
    # ─────────────────────────────────────────────────────

    def refresh(self):
        from database import Producto, Pedido, MovimientoStock
        from utils.helpers import get_alertas, fmt_fecha, fmt_qty
        from datetime import datetime, date

        try:
            with self.get_session() as s:
                # KPIs
                n_prod = s.query(Producto).filter(Producto.estado == "activo").count()
                n_ped  = (s.query(Pedido)
                          .filter(Pedido.estado.in_(["borrador", "pendiente", "enviado"]))
                          .count())
                alertas = get_alertas(s)
                hoy     = date.today()
                n_mov   = (s.query(MovimientoStock)
                           .filter(MovimientoStock.fecha >= datetime.combine(hoy, datetime.min.time()))
                           .count())

                self.kpi_productos.configure(text=str(n_prod))
                self.kpi_pedidos.configure(text=str(n_ped))
                self.kpi_alertas.configure(text=str(alertas["total"]))
                self.kpi_mov.configure(text=str(n_mov))

                # Alertas
                for w in self.alertas_inner.winfo_children():
                    w.destroy()

                if alertas["total"] == 0:
                    ctk.CTkLabel(
                        self.alertas_inner, text="✔  Sin alertas activas.",
                        text_color=COLOR_SUCCESS, font=ctk.CTkFont(size=12),
                    ).pack(anchor="w")
                else:
                    for p in alertas["stock_bajo"][:5]:
                        self._alerta_item(
                            self.alertas_inner, "📦",
                            f"Stock bajo: {p.nombre} ({fmt_qty(p.cantidad_actual, p.unidad)} / mín {fmt_qty(p.cantidad_minima, p.unidad)})",
                            COLOR_INFO,
                        )
                    for l in alertas["por_caducar"][:5]:
                        dias = (l.fecha_caducidad - date.today()).days
                        self._alerta_item(
                            self.alertas_inner, "⏳",
                            f"Por caducar ({dias}d): {l.producto.nombre} — lote {l.numero_lote or '—'}",
                            COLOR_WARNING,
                        )
                    for l in alertas["caducados"][:5]:
                        self._alerta_item(
                            self.alertas_inner, "❌",
                            f"Caducado: {l.producto.nombre} — lote {l.numero_lote or '—'}",
                            COLOR_DANGER,
                        )

                # Últimos movimientos
                for row in self.mov_tree.get_children():
                    self.mov_tree.delete(row)

                movs = (s.query(MovimientoStock)
                        .order_by(MovimientoStock.fecha.desc())
                        .limit(20)
                        .all())
                for m in movs:
                    self.mov_tree.insert("", "end", values=(
                        fmt_fecha(m.fecha),
                        m.tipo,
                        m.producto.nombre if m.producto else "—",
                        fmt_qty(m.cantidad),
                        m.usuario.nombre if m.usuario else "—",
                    ))

                # Productos críticos
                for row in self.crit_tree.get_children():
                    self.crit_tree.delete(row)

                criticos = alertas["stock_bajo"][:15]
                for p in criticos:
                    self.crit_tree.insert("", "end", values=(
                        p.nombre,
                        fmt_qty(p.cantidad_actual),
                        fmt_qty(p.cantidad_minima),
                    ))

        except Exception as exc:
            import traceback
            traceback.print_exc()

    def _alerta_item(self, parent, icon, text, color):
        row = ctk.CTkFrame(parent, fg_color="transparent", height=26)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)
        ctk.CTkLabel(row, text=f"{icon}  {text}",
                     font=ctk.CTkFont(size=11), text_color=color,
                     anchor="w").pack(side="left")
