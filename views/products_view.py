"""
products_view.py — Gestión completa de productos
"""

import os
import sys
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from views.base_view import BaseView, ModalBase, apply_treeview_style
from config import COLOR_ACCENT, COLOR_ACCENT_HOVER, COLOR_DANGER, COLOR_WARNING, COLOR_CARD_BG


class ProductosView(BaseView):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        apply_treeview_style()
        self._build()
        self.refresh()

    # ─────────────────────────────────────────────────────
    #  UI
    # ─────────────────────────────────────────────────────

    def _build(self):
        # Cabecera
        hdr = self.make_header(self, "Productos",
                               "+ Nuevo Producto", self._nuevo)
        hdr.pack(fill="x")

        # Filtros
        fil = ctk.CTkFrame(self, fg_color="#21262d", height=52, corner_radius=0)
        fil.pack(fill="x")
        fil.pack_propagate(False)

        self._search_var = tk.StringVar()
        ctk.CTkEntry(
            fil, textvariable=self._search_var,
            placeholder_text="Buscar nombre, referencia o lote…",
            width=280, height=32,
        ).pack(side="left", padx=10, pady=10)

        self._cat_var = tk.StringVar(value="Todas")
        self._cat_cb = ctk.CTkComboBox(fil, variable=self._cat_var,
                                        values=["Todas"], width=150, height=32,
                                        state="readonly")
        self._cat_cb.pack(side="left", padx=4, pady=10)

        self._estado_var = tk.StringVar(value="activo")
        ctk.CTkComboBox(
            fil, variable=self._estado_var,
            values=["todos", "activo", "consumido", "baja"],
            width=110, height=32, state="readonly",
        ).pack(side="left", padx=4, pady=10)

        self._stock_bajo_var = tk.BooleanVar()
        ctk.CTkCheckBox(fil, text="Solo stock bajo",
                        variable=self._stock_bajo_var,
                        font=ctk.CTkFont(size=12)).pack(side="left", padx=8)

        ctk.CTkButton(fil, text="Buscar", command=self.refresh,
                      width=80, height=32,
                      fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER).pack(side="left", padx=4)

        # Tabla
        cols = [
            ("nombre",    "Nombre",      220),
            ("ref",       "Referencia",  120),
            ("categoria", "Categoría",   130),
            ("stock",     "Stock",        80, "e"),
            ("minimo",    "Mínimo",       70, "e"),
            ("unidad",    "Unidad",       80),
            ("lote",      "Lote",        110),
            ("caducidad", "Caducidad",   100),
            ("estado",    "Estado",       80),
            ("ubicacion", "Ubicación",   110),
        ]
        tframe, self.tree = self.make_sortable_table(self, cols)
        tframe.pack(fill="both", expand=True, padx=10, pady=6)
        self.tree.bind("<Double-1>", lambda _: self._ver_detalle())

        # Botones de acción inferiores
        bar = ctk.CTkFrame(self, fg_color="transparent", height=44)
        bar.pack(fill="x", padx=10, pady=(0, 6))
        bar.pack_propagate(False)

        ctk.CTkButton(bar, text="Ver detalle", command=self._ver_detalle,
                      width=120, height=32).pack(side="left", padx=4)
        ctk.CTkButton(bar, text="🧪 Ver lotes", command=self._ver_lotes,
                      fg_color="#1e3a5f", hover_color="#1e40af",
                      width=110, height=32).pack(side="left", padx=4)
        ctk.CTkButton(bar, text="Editar", command=self._editar,
                      fg_color="#374151", hover_color="#4b5563",
                      width=90, height=32).pack(side="left", padx=4)

        ctk.CTkButton(bar, text="📥 Exportar CSV", command=self._exportar_csv,
                      fg_color="#374151", hover_color="#4b5563",
                      width=130, height=32).pack(side="right", padx=4)

    # ─────────────────────────────────────────────────────
    #  DATOS
    # ─────────────────────────────────────────────────────

    def refresh(self):
        from database import Producto, Categoria
        from utils.helpers import fmt_fecha_corta, fmt_qty

        # Actualizar combo de categorías
        try:
            with self.get_session() as s:
                cats = [c.nombre for c in s.query(Categoria).order_by(Categoria.nombre).all()]
            self._cat_cb.configure(values=["Todas"] + cats)
        except Exception:
            pass

        # Limpiar tabla
        for row in self.tree.get_children():
            self.tree.delete(row)

        search    = self._search_var.get().strip().lower()
        cat_fil   = self._cat_var.get()
        estado_fil = self._estado_var.get()
        solo_bajo  = self._stock_bajo_var.get()

        try:
            with self.get_session() as s:
                q = s.query(Producto)
                if estado_fil != "todos":
                    q = q.filter(Producto.estado == estado_fil)
                if cat_fil != "Todas":
                    cat = s.query(Categoria).filter_by(nombre=cat_fil).first()
                    if cat:
                        q = q.filter(Producto.categoria_id == cat.id)
                productos = q.order_by(Producto.nombre).all()

                for p in productos:
                    if search:
                        hay = f"{p.nombre} {p.referencia}".lower()
                        if search not in hay:
                            continue
                    if solo_bajo and not p.stock_bajo:
                        continue

                    tags = ()
                    if p.stock_bajo:
                        tags = ("stock_bajo",)

                    self.tree.insert("", "end", iid=str(p.id), values=(
                        p.nombre,
                        p.referencia,
                        p.categoria.nombre if p.categoria else "—",
                        fmt_qty(p.cantidad_actual),
                        fmt_qty(p.cantidad_minima),
                        p.nombre_unidad or "—",
                        "—",
                        "-",
                        p.estado,
                        p.nombre_ubicacion or "—",
                    ), tags=tags)

        except Exception as exc:
            self.show_error(str(exc))

        self.tree.tag_configure("caducado",    background="#4a1212")
        self.tree.tag_configure("por_caducar", background="#4a3212")
        self.tree.tag_configure("stock_bajo",  background="#122a4a")

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            self.show_error("Selecciona un producto primero.")
            return None
        return int(sel[0])

    def _ver_detalle(self):
        pid = self._selected_id()
        if pid:
            DetalleProductoModal(self, pid)

    def _ver_lotes(self):
        pid = self._selected_id()
        if not pid:
            return
        from database import Producto
        try:
            with self.get_session() as s:
                p = s.query(Producto).get(pid)
                if not p:
                    return
                if not (p.tiene_lote or p.tiene_caducidad):
                    self.show_info("Este producto no usa lotes ni tiene fecha de caducidad.")
                    return
                nombre = p.nombre
        except Exception as exc:
            self.show_error(str(exc))
            return
        LotesProductoModal(self, pid, nombre)

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
            title="Exportar productos",
            defaultextension=".csv",
            initialfile=f"productos_{fecha_str}.csv",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
        )
        if not path:
            return

        headers = ["Nombre", "Referencia", "Categoría", "Stock", "Mínimo",
                   "Unidad", "Lote", "Caducidad", "Estado", "Ubicación"]
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(headers)
                w.writerows(rows)
            self.show_info(f"Exportado correctamente:\n{path}")
        except Exception as exc:
            self.show_error(str(exc))

    def _nuevo(self):
        m = ProductoFormModal(self, None, self.current_user)
        self.wait_window(m)
        self.refresh()

    def _editar(self):
        pid = self._selected_id()
        if pid:
            m = ProductoFormModal(self, pid, self.current_user)
            self.wait_window(m)
            self.refresh()


# ─────────────────────────────────────────────────────────
#  MODAL DETALLE
# ─────────────────────────────────────────────────────────

class DetalleProductoModal(ModalBase):
    def __init__(self, parent, producto_id: int):
        super().__init__(parent, "Detalle de Producto", ancho=680, alto=560)
        self._pid = producto_id
        self._load()
        # Solo botón Cerrar
        ctk.CTkButton(self.btn_bar, text="Cerrar", command=self.destroy,
                      fg_color="#374151", hover_color="#4b5563",
                      width=100).pack(side="right")

    def _load(self):
        from database import Producto, MovimientoStock
        from utils.helpers import fmt_fecha, fmt_fecha_corta, fmt_qty

        try:
            with self._get_session() as s:
                p = s.query(Producto).get(self._pid)
                if not p:
                    return

                # Campos informativos
                campos = [
                    ("Nombre",       p.nombre),
                    ("Referencia",   p.referencia),
                    ("Categoría",    p.categoria.nombre if p.categoria else "—"),
                    ("Proveedor",    p.proveedor.nombre if p.proveedor else "—"),
                    ("Stock actual", fmt_qty(p.cantidad_actual, p.nombre_unidad)),
                    ("Stock mínimo", fmt_qty(p.cantidad_minima, p.nombre_unidad)),
                    ("Usa lotes",    "Sí" if p.tiene_lote else "No"),
                    ("Caduca",       "Sí" if p.tiene_caducidad else "No"),
                    ("Lotes activos", str(len(p.lotes))),
                    ("Estado",       p.estado),
                    ("Ubicación",    p.nombre_ubicacion or "—"),
                    ("Descripción",  p.descripcion or "—"),
                ]
                for i, (lbl, val) in enumerate(campos):
                    ctk.CTkLabel(
                        self.content, text=f"{lbl}:",
                        font=ctk.CTkFont(size=11), text_color="#9ca3af", anchor="e",
                    ).grid(row=i, column=0, sticky="e", padx=(4, 8), pady=2)
                    ctk.CTkLabel(
                        self.content, text=val,
                        font=ctk.CTkFont(size=12), text_color="white", anchor="w",
                    ).grid(row=i, column=1, sticky="w", padx=4, pady=2)

                self.content.grid_columnconfigure(1, weight=1)

                # Historial
                row_sep = len(campos)
                ctk.CTkLabel(
                    self.content, text="Últimos movimientos",
                    font=ctk.CTkFont(size=13, weight="bold"), text_color="white",
                ).grid(row=row_sep, column=0, columnspan=2, sticky="w",
                       padx=4, pady=(14, 4))

                from views.base_view import apply_treeview_style
                apply_treeview_style()
                tree_frame = ctk.CTkFrame(self.content, fg_color="#1c1c1c", corner_radius=6)
                tree_frame.grid(row=row_sep+1, column=0, columnspan=2,
                                sticky="ew", padx=4, pady=(0, 6))
                self.content.grid_rowconfigure(row_sep+1, weight=1)

                from tkinter import ttk
                ht = ttk.Treeview(
                    tree_frame,
                    columns=("fecha", "tipo", "cantidad", "antes", "despues", "motivo"),
                    show="headings", style="LabTrack.Treeview", height=6,
                )
                for cid, ctxt, cw in [
                    ("fecha", "Fecha", 120), ("tipo", "Tipo", 80),
                    ("cantidad", "Cant.", 70), ("antes", "Antes", 70),
                    ("despues", "Después", 70), ("motivo", "Motivo", 200),
                ]:
                    ht.heading(cid, text=ctxt); ht.column(cid, width=cw, anchor="w")

                movs = (s.query(MovimientoStock)
                        .filter_by(producto_id=self._pid)
                        .order_by(MovimientoStock.fecha.desc())
                        .limit(20).all())
                for m in movs:
                    ht.insert("", "end", values=(
                        fmt_fecha(m.fecha), m.tipo,
                        fmt_qty(m.cantidad),
                        fmt_qty(m.cantidad_anterior),
                        fmt_qty(m.cantidad_posterior),
                        m.motivo or "—",
                    ))

                vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=ht.yview,
                                    style="LabTrack.Vertical.TScrollbar")
                ht.configure(yscrollcommand=vsb.set)
                ht.grid(row=0, column=0, sticky="nsew")
                vsb.grid(row=0, column=1, sticky="ns")
                tree_frame.grid_rowconfigure(0, weight=1)
                tree_frame.grid_columnconfigure(0, weight=1)

        except Exception as exc:
            import traceback; traceback.print_exc()

    def _get_session(self):
        from database import get_session
        return get_session()


# ─────────────────────────────────────────────────────────
#  MODAL VER LOTES
# ─────────────────────────────────────────────────────────

class LotesProductoModal(ModalBase):
    def __init__(self, parent, producto_id: int, nombre: str):
        super().__init__(parent, f"Lotes — {nombre}", ancho=620, alto=420)
        self._pid = producto_id
        self._load()
        ctk.CTkButton(self.btn_bar, text="Cerrar", command=self.destroy,
                      fg_color="#374151", hover_color="#4b5563",
                      width=100).pack(side="right")

    def _load(self):
        from database import LoteProducto, get_session
        from utils.helpers import fmt_fecha_corta
        from datetime import date

        apply_treeview_style()
        tf = ctk.CTkFrame(self.content, fg_color="#1c1c1c", corner_radius=6)
        tf.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=4, pady=4)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        from tkinter import ttk
        tree = ttk.Treeview(
            tf,
            columns=("lote", "cantidad", "caducidad", "dias"),
            show="headings", style="LabTrack.Treeview",
        )
        for cid, ctxt, cw, anch in [
            ("lote",      "Nº Lote",        180, "w"),
            ("cantidad",  "Cantidad",         90, "e"),
            ("caducidad", "Caducidad",       110, "w"),
            ("dias",      "Días restantes",  120, "e"),
        ]:
            tree.heading(cid, text=ctxt, anchor=anch)
            tree.column(cid, width=cw, anchor=anch)

        vsb = ttk.Scrollbar(tf, orient="vertical", command=tree.yview,
                            style="LabTrack.Vertical.TScrollbar")
        tree.configure(yscrollcommand=vsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        tf.grid_rowconfigure(0, weight=1)
        tf.grid_columnconfigure(0, weight=1)

        tree.tag_configure("caducado",    foreground="#ef4444")
        tree.tag_configure("por_caducar", foreground="#f59e0b")

        try:
            with get_session() as s:
                lotes = (s.query(LoteProducto)
                         .filter_by(producto_id=self._pid)
                         .order_by(LoteProducto.fecha_caducidad.asc())
                         .all())
                today = date.today()
                for lt in lotes:
                    if lt.fecha_caducidad:
                        dias = (lt.fecha_caducidad - today).days
                        cad_str = fmt_fecha_corta(lt.fecha_caducidad)
                        dias_str = str(dias)
                        if dias < 0:
                            tag = ("caducado",)
                        elif dias < 30:
                            tag = ("por_caducar",)
                        else:
                            tag = ()
                    else:
                        dias_str = "—"
                        cad_str  = "—"
                        tag      = ()

                    tree.insert("", "end", values=(
                        lt.numero_lote or "—",
                        lt.cantidad,
                        cad_str,
                        dias_str,
                    ), tags=tag)
        except Exception as exc:
            import traceback; traceback.print_exc()


# ─────────────────────────────────────────────────────────
#  MODAL CREAR / EDITAR
# ─────────────────────────────────────────────────────────

class ProductoFormModal(ModalBase):
    def __init__(self, parent, producto_id, current_user):
        titulo = "Nuevo Producto" if producto_id is None else "Editar Producto"
        super().__init__(parent, titulo, ancho=540, alto=660)
        self._pid  = producto_id
        self._user = current_user
        self._build_form()
        if producto_id:
            self._load_data()
        self.add_buttons(self._guardar)

    def _get_session(self):
        from database import get_session
        return get_session()

    def _build_form(self):
        from database import Categoria, Proveedor, Unidad, Ubicacion, ESTADOS_PRODUCTO

        r = 0
        self.add_label("Nombre *", r); r += 1
        self.e_nombre = self.add_entry(r, "Nombre del producto"); r += 1

        self.add_label("Referencia *", r); r += 1
        self.e_ref = self.add_entry(r, "Código / referencia única"); r += 1

        with self._get_session() as s:
            cats  = [c.nombre for c in s.query(Categoria).order_by(Categoria.nombre).all()]
            provs = [p.nombre for p in s.query(Proveedor).filter_by(activo=True).order_by(Proveedor.nombre).all()]
            units = [u.nombre for u in s.query(Unidad).order_by(Unidad.nombre).all()]
            ubics = [u.nombre for u in s.query(Ubicacion).order_by(Ubicacion.nombre).all()]

        self.add_label("Categoría", r); r += 1
        self.e_cat = self.add_combo(r, ["— Sin categoría —"] + cats); r += 1

        self.add_label("Proveedor", r); r += 1
        self.e_prov = self.add_combo(r, ["— Sin proveedor —"] + provs); r += 1

        self.add_label("Stock actual", r); r += 1
        self.e_stock = self.add_entry(r, "0"); r += 1

        self.add_label("Stock mínimo (alerta)", r); r += 1
        self.e_min = self.add_entry(r, "0"); r += 1

        self.add_label("Unidad", r); r += 1
        self.e_unidad = self.add_combo(r, units if units else ["unidades"]); r += 1

        self.add_label("Trazabilidad", r); r += 1
        self._tiene_lote_var = tk.BooleanVar(value=False)
        self._tiene_cad_var  = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.content, text="Este producto usa números de lote",
                        variable=self._tiene_lote_var).grid(
            row=r, column=0, columnspan=2, sticky="w", padx=4, pady=2); r += 1
        ctk.CTkCheckBox(self.content, text="Este producto tiene fecha de caducidad",
                        variable=self._tiene_cad_var).grid(
            row=r, column=0, columnspan=2, sticky="w", padx=4, pady=2); r += 1

        self.add_label("Ubicación", r); r += 1
        self.e_ubic = self.add_combo(r, ["— Sin ubicación —"] + ubics); r += 1

        self.add_label("Estado", r); r += 1
        self.e_estado = self.add_combo(r, ESTADOS_PRODUCTO); r += 1

        self.add_label("Descripción", r); r += 1
        self.e_desc = self.add_textbox(r, height=60); r += 1

    def _load_data(self):
        from database import Producto

        with self._get_session() as s:
            p = s.query(Producto).get(self._pid)
            if not p:
                return

            def _set(entry, val):
                entry.delete(0, "end")
                entry.insert(0, str(val) if val is not None else "")

            _set(self.e_nombre, p.nombre)
            _set(self.e_ref,    p.referencia)

            if p.categoria:
                self.e_cat.set(p.categoria.nombre)
            if p.proveedor:
                self.e_prov.set(p.proveedor.nombre)

            _set(self.e_stock, int(p.cantidad_actual) if p.cantidad_actual == int(p.cantidad_actual) else p.cantidad_actual)
            _set(self.e_min,   int(p.cantidad_minima) if p.cantidad_minima == int(p.cantidad_minima) else p.cantidad_minima)

            unidad_nombre = p.nombre_unidad
            if unidad_nombre:
                self.e_unidad.set(unidad_nombre)

            self._tiene_lote_var.set(bool(p.tiene_lote))
            self._tiene_cad_var.set(bool(p.tiene_caducidad))

            ubic_nombre = p.nombre_ubicacion
            if ubic_nombre:
                self.e_ubic.set(ubic_nombre)

            self.e_estado.set(p.estado or "activo")
            self.set_tb(self.e_desc, p.descripcion or "")

    def _guardar(self):
        from database import Producto, Categoria, Proveedor, Unidad, Ubicacion

        nombre = self.e_nombre.get().strip()
        ref    = self.e_ref.get().strip()
        if not nombre or not ref:
            self.show_error("Nombre y Referencia son obligatorios.")
            return

        try:
            stock = float(self.e_stock.get() or "0")
            mini  = float(self.e_min.get() or "0")
        except ValueError:
            self.show_error("Stock y mínimo deben ser números.")
            return

        with self._get_session() as s:
            # Resolver IDs
            cat_nombre   = self.e_cat.get()
            prov_nombre  = self.e_prov.get()
            unit_nombre  = self.e_unidad.get()
            ubic_nombre  = self.e_ubic.get()
            cat_id = prov_id = unit_id = ubic_id = None

            if cat_nombre and "Sin" not in cat_nombre:
                cat = s.query(Categoria).filter_by(nombre=cat_nombre).first()
                if cat:
                    cat_id = cat.id
            if prov_nombre and "Sin" not in prov_nombre:
                prov = s.query(Proveedor).filter_by(nombre=prov_nombre).first()
                if prov:
                    prov_id = prov.id
            if unit_nombre:
                unit = s.query(Unidad).filter_by(nombre=unit_nombre).first()
                if unit:
                    unit_id = unit.id
            if ubic_nombre and "Sin" not in ubic_nombre:
                ubic = s.query(Ubicacion).filter_by(nombre=ubic_nombre).first()
                if ubic:
                    ubic_id = ubic.id

            if self._pid is None:
                if s.query(Producto).filter_by(referencia=ref).first():
                    self.show_error(f"Ya existe un producto con referencia '{ref}'.")
                    return
                p = Producto()
                s.add(p)
            else:
                p = s.query(Producto).get(self._pid)
                existing = s.query(Producto).filter(
                    Producto.referencia == ref,
                    Producto.id != self._pid,
                ).first()
                if existing:
                    self.show_error(f"Ya existe otro producto con referencia '{ref}'.")
                    return

            p.nombre          = nombre
            p.referencia      = ref
            p.categoria_id    = cat_id
            p.proveedor_id    = prov_id
            p.cantidad_actual = stock
            p.cantidad_minima = mini
            p.unidad          = unit_nombre   # mantener texto legacy
            p.unidad_id       = unit_id
            p.tiene_lote      = self._tiene_lote_var.get()
            p.tiene_caducidad = self._tiene_cad_var.get()
            p.ubicacion       = ubic_nombre if ubic_nombre and "Sin" not in ubic_nombre else None
            p.ubicacion_id    = ubic_id
            p.estado          = self.e_estado.get()
            p.descripcion     = self.get_tb(self.e_desc) or None

            s.commit()

        self.destroy()

    def show_error(self, msg):
        from tkinter import messagebox
        messagebox.showerror("Error", msg, parent=self)
