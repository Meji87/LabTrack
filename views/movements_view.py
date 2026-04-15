"""
movements_view.py — Historial de movimientos y registro de consumo/entrada/baja
"""

import os
import sys
import tkinter as tk
import customtkinter as ctk
from datetime import date, timedelta

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from views.base_view import BaseView, ModalBase, apply_treeview_style
from config import COLOR_ACCENT, COLOR_ACCENT_HOVER, COLOR_DANGER, COLOR_WARNING, COLOR_SUCCESS


_TIPO_COLORS = {
    "entrada":   "#14532d",
    "recepcion": "#14532d",
    "consumo":   "#1e3a5f",
    "baja":      "#4a1212",
    "ajuste":    "#374151",
}


class MovimientosView(BaseView):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        apply_treeview_style()
        self._build()
        self.refresh()

    def _build(self):
        hdr = self.make_header(self, "Movimientos de Stock")
        hdr.pack(fill="x")

        # Filtros
        fil = ctk.CTkFrame(self, fg_color="#21262d", height=52, corner_radius=0)
        fil.pack(fill="x")
        fil.pack_propagate(False)

        self._tipo_var = tk.StringVar(value="todos")
        ctk.CTkComboBox(
            fil, variable=self._tipo_var,
            values=["todos", "entrada", "consumo", "baja", "ajuste", "recepcion"],
            width=130, height=32, state="readonly",
        ).pack(side="left", padx=10, pady=10)

        ctk.CTkLabel(fil, text="Desde:", text_color="#9ca3af",
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(8, 4))
        #self._desde_var = tk.StringVar(value=(date.today() - timedelta(days=30)).strftime("%d/%m/%Y"))
        #ctk.CTkEntry(fil, textvariable=self._desde_var, width=100, height=32).pack(side="left", padx=(0, 8))
        self._desde_var = tk.StringVar(value=(date.today() - timedelta(days=30)).strftime("%d/%m/%Y"))
        desde_entry = ctk.CTkEntry(fil, textvariable=self._desde_var, width=100, height=32)
        desde_entry.pack(side="left", padx=(0, 8))
        desde_entry.bind("<Button-1>", lambda e: self._abrir_calendario(self._desde_var, desde_entry))

        ctk.CTkLabel(fil, text="Hasta:", text_color="#9ca3af",
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 4))
        #self._hasta_var = tk.StringVar(value=date.today().strftime("%d/%m/%Y"))
        #ctk.CTkEntry(fil, textvariable=self._hasta_var, width=100, height=32).pack(side="left", padx=(0, 8))
        self._hasta_var = tk.StringVar(value=date.today().strftime("%d/%m/%Y"))
        hasta_entry = ctk.CTkEntry(fil, textvariable=self._hasta_var, width=100, height=32)
        hasta_entry.pack(side="left", padx=(0, 8))
        hasta_entry.bind("<Button-1>", lambda e: self._abrir_calendario(self._hasta_var, hasta_entry))

        ctk.CTkButton(fil, text="Filtrar", command=self.refresh,
                      width=80, height=32,
                      fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER).pack(side="left", padx=4)

        # Tabla
        cols = [
            ("fecha",    "Fecha",        130),
            ("tipo",     "Tipo",          80),
            ("producto", "Producto",     220),
            ("cantidad", "Cantidad",      80, "e"),
            ("antes",    "Antes",         70, "e"),
            ("despues",  "Después",       70, "e"),
            ("usuario",  "Usuario",      110),
            ("motivo",   "Motivo",       220),
        ]
        tframe, self.tree = self.make_sortable_table(self, cols)
        tframe.pack(fill="both", expand=True, padx=10, pady=6)

        # Botones de acción
        bar = ctk.CTkFrame(self, fg_color="transparent", height=50)
        bar.pack(fill="x", padx=10, pady=(0, 8))
        bar.pack_propagate(False)

        ctk.CTkButton(bar, text="📥 Exportar CSV", command=self._exportar_csv,
                      fg_color="#374151", hover_color="#4b5563",
                      width=130, height=36).pack(side="right", padx=4)

        ctk.CTkLabel(bar, text="Registrar:",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#9ca3af").pack(side="left", padx=(4, 12))

        ctk.CTkButton(bar, text="📦 Entrada", command=self._nueva_entrada,
                      fg_color=COLOR_SUCCESS, hover_color="#16a34a",
                      width=110, height=36).pack(side="left", padx=4)
        ctk.CTkButton(bar, text="🔬 Consumo", command=self._nuevo_consumo,
                      fg_color="#1e3a5f", hover_color="#1e40af",
                      width=110, height=36).pack(side="left", padx=4)
        ctk.CTkButton(bar, text="⚠ Baja", command=self._nueva_baja,
                      fg_color="#7f1d1d", hover_color="#991b1b",
                      width=100, height=36).pack(side="left", padx=4)

    def refresh(self):
        from database import MovimientoStock
        from utils.helpers import fmt_fecha, fmt_qty, parse_fecha
        from datetime import datetime, time

        for row in self.tree.get_children():
            self.tree.delete(row)

        tipo_fil  = self._tipo_var.get()
        desde_str = self._desde_var.get().strip()
        hasta_str = self._hasta_var.get().strip()

        desde_date = parse_fecha(desde_str)
        hasta_date = parse_fecha(hasta_str)

        try:
            with self.get_session() as s:
                q = s.query(MovimientoStock)
                if tipo_fil != "todos":
                    q = q.filter(MovimientoStock.tipo == tipo_fil)
                if desde_date:
                    q = q.filter(MovimientoStock.fecha >= datetime.combine(desde_date, time.min))
                if hasta_date:
                    q = q.filter(MovimientoStock.fecha <= datetime.combine(hasta_date, time.max))
                movs = q.order_by(MovimientoStock.fecha.desc()).limit(500).all()

                for m in movs:
                    self.tree.insert("", "end", values=(
                        fmt_fecha(m.fecha),
                        m.tipo,
                        m.producto.nombre if m.producto else "—",
                        fmt_qty(m.cantidad),
                        fmt_qty(m.cantidad_anterior),
                        fmt_qty(m.cantidad_posterior),
                        m.usuario.nombre if m.usuario else "—",
                        m.motivo or "—",
                    ), tags=(m.tipo,))

        except Exception as exc:
            self.show_error(str(exc))

        for tipo, bg in _TIPO_COLORS.items():
            self.tree.tag_configure(tipo, background=bg)

    def _nueva_entrada(self):
        m = MovimientoModal(self, "entrada", self.current_user, self.get_session)
        self.wait_window(m)
        self.refresh()

    def _nuevo_consumo(self):
        m = MovimientoModal(self, "consumo", self.current_user, self.get_session)
        self.wait_window(m)
        self.refresh()

    def _nueva_baja(self):
        m = MovimientoModal(self, "baja", self.current_user, self.get_session)
        self.wait_window(m)
        self.refresh()

    def _exportar_csv(self):
        from tkinter import filedialog
        import csv
        from datetime import datetime

        rows = []
        for iid in self.tree.get_children():
            rows.append(self.tree.item(iid, "values"))

        if not rows:
            self.show_info("No hay datos para exportar.")
            return

        fecha_str = datetime.now().strftime("%Y%m%d")
        path = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(),
            title="Exportar movimientos",
            defaultextension=".csv",
            initialfile=f"movimientos_{fecha_str}.csv",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
        )
        if not path:
            return

        headers = ["Fecha", "Tipo", "Producto", "Cantidad", "Antes", "Después", "Usuario", "Motivo"]
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(headers)
                w.writerows(rows)
            self.show_info(f"Exportado correctamente:\n{path}")
        except Exception as exc:
            self.show_error(str(exc))

    def _abrir_calendario(self, var: tk.StringVar, widget):
        from tkcalendar import Calendar
        import datetime

        top = ctk.CTkToplevel(self)
        top.title("")
        top.resizable(False, False)
        top.grab_set()
        self.after(200, lambda: self._set_icon_on(top))

        # Posicionar justo debajo del widget
        top.update_idletasks()
        wx = widget.winfo_rootx()
        wy = widget.winfo_rooty() + widget.winfo_height()
        top.geometry(f"+{wx}+{wy}")

        # Parsear fecha actual del campo
        try:
            d = datetime.datetime.strptime(var.get(), "%d/%m/%Y").date()
        except ValueError:
            d = datetime.date.today()

        cal = Calendar(
            top,
            selectmode="day",
            year=d.year, month=d.month, day=d.day,
            date_pattern="dd/mm/yyyy",
            background="#1e2329",
            foreground="white",
            headersbackground="#111827",
            headersforeground="#9ca3af",
            selectbackground="#10b981",
            selectforeground="white",
            normalbackground="#1e2329",
            normalforeground="white",
            weekendbackground="#1e2329",
            weekendforeground="#9ca3af",
            othermonthbackground="#111827",
            othermonthforeground="#4b5563",
            bordercolor="#2d333b",
            locale="es_ES",
        )
        cal.pack(padx=8, pady=8)

        def _seleccionar():
            var.set(cal.get_date())
            top.destroy()

        ctk.CTkButton(top, text="Seleccionar", command=_seleccionar,
                    height=30, fg_color="#10b981", hover_color="#059669").pack(pady=(0, 8))
        
    def _set_icon_on(self, window):
        app = self.app  # acceso directo a LabTrackApp
        if hasattr(app, '_ico_path') and os.path.isfile(app._ico_path):
            try:
                window.iconbitmap(app._ico_path)
            except Exception:
                pass


# ─────────────────────────────────────────────────────────
#  MODAL GENÉRICO DE MOVIMIENTO
# ─────────────────────────────────────────────────────────

_TIPO_INFO = {
    "entrada":  ("Entrada de Stock",   "Aumenta el stock del producto.",  COLOR_SUCCESS),
    "consumo":  ("Consumo de Producto","Reduce el stock (uso en laboratorio).", "#3b82f6"),
    "baja":     ("Baja de Producto",   "Elimina stock (pérdida, caducidad, etc.).", COLOR_DANGER),
}


class MovimientoModal(ctk.CTkToplevel):

    def __init__(self, parent, tipo: str, current_user, get_session_fn):
        titulo, desc, color = _TIPO_INFO.get(tipo, (tipo, "", "#fff"))
        super().__init__(parent)
        self.title(titulo)
        self.geometry("520x500")
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()
        self._tipo    = tipo
        self._user    = current_user
        self._get_session = get_session_fn
        self._color   = color

        # Campos de lote/caducidad (se crean dinámicamente)
        self._lote_entry:      ctk.CTkEntry   = None
        self._cad_var:         tk.StringVar   = None
        self._lote_sel_var:    tk.StringVar   = None
        self._lotes_disponibles: list[dict]   = []

        self.update_idletasks()
        x = (self.winfo_screenwidth() - 520) // 2
        y = (self.winfo_screenheight() - 500) // 2
        self.geometry(f"+{x}+{y}")

        self._build(titulo, desc, color)
        self.after(200, self._set_icon)

    def _set_icon(self):
        app = self.master
        while app and not hasattr(app, '_ico_path'):
            app = getattr(app, 'master', None)
        if app and hasattr(app, '_ico_path') and os.path.isfile(app._ico_path):
            try:
                self.iconbitmap(app._ico_path)
            except Exception:
                pass

    def _build(self, titulo, desc, color):
        from database import Producto

        # Header
        hdr = ctk.CTkFrame(self, height=60, fg_color="#111827", corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=titulo,
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=color).pack(side="left", padx=16, pady=8)

        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=12)
        body.grid_columnconfigure(0, weight=1)
        self._body = body

        ctk.CTkLabel(body, text=desc, text_color="#9ca3af",
                     font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", pady=(0, 12))

        # Producto
        ctk.CTkLabel(body, text="Producto *", text_color="#9ca3af",
                     font=ctk.CTkFont(size=12), anchor="w").grid(
            row=1, column=0, sticky="w", pady=(0, 2))

        with self._get_session() as s:
            prods = s.query(Producto).filter_by(estado="activo").order_by(Producto.nombre).all()
            self._prod_map = {
                f"{p.nombre} [{p.referencia}]  —  stock: {int(p.cantidad_actual) if p.cantidad_actual == int(p.cantidad_actual) else p.cantidad_actual} {p.nombre_unidad}": p.id
                for p in prods
            }

        self._prod_var = tk.StringVar()
        self._prod_cb = ctk.CTkComboBox(
            body, variable=self._prod_var,
            values=list(self._prod_map.keys()),
            width=460, height=32, state="readonly",
            command=self._on_product_change,
        )
        self._prod_cb.grid(row=2, column=0, sticky="ew", pady=(0, 6))

        # Frame para campos dinámicos de lote
        self._extra_frame = ctk.CTkFrame(body, fg_color="transparent")
        self._extra_frame.grid(row=3, column=0, sticky="ew")
        self._extra_frame.grid_columnconfigure(0, weight=1)

        # Cantidad
        ctk.CTkLabel(body, text="Cantidad *", text_color="#9ca3af",
                     font=ctk.CTkFont(size=12), anchor="w").grid(
            row=4, column=0, sticky="w", pady=(0, 2))
        self._cant_entry = ctk.CTkEntry(body, height=32, placeholder_text="Ej: 5")
        self._cant_entry.grid(row=5, column=0, sticky="ew", pady=(0, 10))

        # Motivo
        ctk.CTkLabel(body, text="Motivo / Notas", text_color="#9ca3af",
                     font=ctk.CTkFont(size=12), anchor="w").grid(
            row=6, column=0, sticky="w", pady=(0, 2))
        self._motivo_tb = ctk.CTkTextbox(body, height=70)
        self._motivo_tb.grid(row=7, column=0, sticky="ew", pady=(0, 10))

        # Referencia doc
        ctk.CTkLabel(body, text="Referencia documento (opcional)", text_color="#9ca3af",
                     font=ctk.CTkFont(size=12), anchor="w").grid(
            row=8, column=0, sticky="w", pady=(0, 2))
        self._ref_entry = ctk.CTkEntry(body, height=32, placeholder_text="Nº albarán, factura…")
        self._ref_entry.grid(row=9, column=0, sticky="ew")

        # Botones
        btn_bar = ctk.CTkFrame(self, fg_color="transparent", height=52)
        btn_bar.pack(fill="x", padx=20, pady=(0, 12))
        btn_bar.pack_propagate(False)

        ctk.CTkButton(btn_bar, text="Cancelar", command=self.destroy,
                      fg_color="#374151", hover_color="#4b5563",
                      width=100, height=34).pack(side="right", padx=4)
        ctk.CTkButton(btn_bar, text="Registrar", command=self._guardar,
                      fg_color=color, hover_color="#059669" if color == COLOR_SUCCESS else color,
                      width=120, height=34).pack(side="right", padx=4)

    def _on_product_change(self, choice):
        """Muestra campos de lote/caducidad según el tipo de movimiento y producto."""
        from database import Producto, LoteProducto

        # Limpiar frame extra
        for w in self._extra_frame.winfo_children():
            w.destroy()
        self._lote_entry   = None
        self._cad_var      = None
        self._lote_sel_var = None
        self._lotes_disponibles = []

        prod_id = self._prod_map.get(choice)
        if not prod_id:
            return

        with self._get_session() as s:
            prod = s.query(Producto).get(prod_id)
            if not prod:
                return
            tiene_lote = prod.tiene_lote
            tiene_cad  = prod.tiene_caducidad
            unidad_nom = prod.nombre_unidad

            if self._tipo == "consumo":
                lotes_raw = (s.query(LoteProducto)
                             .filter(LoteProducto.producto_id == prod_id,
                                     LoteProducto.cantidad > 0)
                             .order_by(LoteProducto.fecha_caducidad.asc())
                             .all())
                from utils.helpers import fmt_fecha_corta
                self._lotes_disponibles = [
                    {
                        "id": lt.id,
                        "label": f"Lote {lt.numero_lote or '—'}  |  {lt.cantidad} {unidad_nom}  |  cad: {fmt_fecha_corta(lt.fecha_caducidad) if lt.fecha_caducidad else '—'}",
                    }
                    for lt in lotes_raw
                ]

        r = 0
        if self._tipo == "entrada":
            if tiene_lote:
                ctk.CTkLabel(self._extra_frame, text="Nº Lote", text_color="#9ca3af",
                             font=ctk.CTkFont(size=12), anchor="w").grid(
                    row=r, column=0, sticky="w", pady=(4, 2)); r += 1
                self._lote_entry = ctk.CTkEntry(self._extra_frame, height=32,
                                                placeholder_text="Número de lote")
                self._lote_entry.grid(row=r, column=0, sticky="ew", pady=(0, 8)); r += 1

            if tiene_cad:
                ctk.CTkLabel(self._extra_frame, text="Fecha de caducidad", text_color="#9ca3af",
                             font=ctk.CTkFont(size=12), anchor="w").grid(
                    row=r, column=0, sticky="w", pady=(4, 2)); r += 1
                self._cad_var = tk.StringVar()
                cad_entry = ctk.CTkEntry(self._extra_frame, textvariable=self._cad_var,
                                         height=32, placeholder_text="DD/MM/AAAA")
                cad_entry.grid(row=r, column=0, sticky="ew", pady=(0, 8)); r += 1
                cad_entry.bind("<Button-1>",
                               lambda e: self._abrir_calendario(self._cad_var, cad_entry))

        elif self._tipo == "consumo" and self._lotes_disponibles:
            ctk.CTkLabel(self._extra_frame, text="Seleccionar lote (opcional)",
                         text_color="#9ca3af",
                         font=ctk.CTkFont(size=12), anchor="w").grid(
                row=r, column=0, sticky="w", pady=(4, 2)); r += 1
            self._lote_sel_var = tk.StringVar()
            labels = [lt["label"] for lt in self._lotes_disponibles]
            ctk.CTkComboBox(self._extra_frame, variable=self._lote_sel_var,
                            values=labels, height=32, state="readonly").grid(
                row=r, column=0, sticky="ew", pady=(0, 8)); r += 1

    def _abrir_calendario(self, var: tk.StringVar, widget):
        from tkcalendar import Calendar
        import datetime

        top = ctk.CTkToplevel(self)
        top.title("")
        top.resizable(False, False)
        top.grab_set()
        top.update_idletasks()
        wx = widget.winfo_rootx()
        wy = widget.winfo_rooty() + widget.winfo_height()
        top.geometry(f"+{wx}+{wy}")

        try:
            d = datetime.datetime.strptime(var.get(), "%d/%m/%Y").date()
        except ValueError:
            d = datetime.date.today()

        cal = Calendar(top, selectmode="day",
                       year=d.year, month=d.month, day=d.day,
                       date_pattern="dd/mm/yyyy",
                       background="#1e2329", foreground="white",
                       headersbackground="#111827", headersforeground="#9ca3af",
                       selectbackground="#10b981", selectforeground="white",
                       normalbackground="#1e2329", normalforeground="white",
                       weekendbackground="#1e2329", weekendforeground="#9ca3af",
                       othermonthbackground="#111827", othermonthforeground="#4b5563",
                       bordercolor="#2d333b")
        cal.pack(padx=8, pady=8)

        def _sel():
            var.set(cal.get_date())
            top.destroy()

        ctk.CTkButton(top, text="Seleccionar", command=_sel,
                      height=30, fg_color="#10b981", hover_color="#059669").pack(pady=(0, 8))

    def _guardar(self):
        from database import Producto, MovimientoStock, LoteProducto
        from utils.helpers import parse_fecha
        from tkinter import messagebox

        prod_key = self._prod_var.get()
        if not prod_key:
            messagebox.showerror("Error", "Selecciona un producto.", parent=self)
            return

        try:
            cant = float(self._cant_entry.get() or "0")
            if cant <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Introduce una cantidad válida mayor que 0.", parent=self)
            return

        prod_id = self._prod_map.get(prod_key)
        motivo  = self._motivo_tb.get("1.0", "end").strip() or None
        ref_doc = self._ref_entry.get().strip() or None

        with self._get_session() as s:
            prod = s.query(Producto).get(prod_id)
            if not prod:
                messagebox.showerror("Error", "Producto no encontrado.", parent=self)
                return

            if self._tipo in ("consumo", "baja") and cant > prod.cantidad_actual:
                messagebox.showerror("Error",
                    f"Stock insuficiente ({prod.cantidad_actual} {prod.nombre_unidad} disponibles).",
                    parent=self)
                return

            antes = prod.cantidad_actual

            if self._tipo == "entrada":
                prod.cantidad_actual += cant
                # Crear lote si hay datos
                numero_lote = self._lote_entry.get().strip() if self._lote_entry else None
                fecha_cad   = parse_fecha(self._cad_var.get()) if self._cad_var else None
                if numero_lote or fecha_cad:
                    s.add(LoteProducto(
                        producto_id=prod.id,
                        numero_lote=numero_lote or None,
                        fecha_caducidad=fecha_cad,
                        cantidad=cant,
                    ))

            elif self._tipo in ("consumo", "baja"):
                prod.cantidad_actual -= cant
                if prod.cantidad_actual <= 0:
                    prod.cantidad_actual = 0
                    prod.estado = "consumido"

                # Descontar del lote seleccionado (consumo)
                if self._tipo == "consumo" and self._lote_sel_var and self._lotes_disponibles:
                    sel_label = self._lote_sel_var.get()
                    lote_id   = next(
                        (lt["id"] for lt in self._lotes_disponibles if lt["label"] == sel_label),
                        None,
                    )
                    if lote_id:
                        lote = s.query(LoteProducto).get(lote_id)
                        if lote:
                            lote.cantidad = max(0.0, lote.cantidad - cant)

            s.add(MovimientoStock(
                producto_id=prod.id,
                usuario_id=self._user.id if self._user else None,
                tipo=self._tipo,
                cantidad=cant,
                cantidad_anterior=antes,
                cantidad_posterior=prod.cantidad_actual,
                motivo=motivo,
                referencia_doc=ref_doc,
            ))
            s.commit()

        self.destroy()
