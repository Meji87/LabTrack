"""
suppliers_view.py — Gestión de proveedores
"""

import os
import sys
import tkinter as tk
import customtkinter as ctk

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from views.base_view import BaseView, ModalBase, apply_treeview_style
from config import COLOR_ACCENT, COLOR_ACCENT_HOVER, COLOR_DANGER


class ProveedoresView(BaseView):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        apply_treeview_style()
        self._build()
        self.refresh()

    def _build(self):
        hdr = self.make_header(self, "Proveedores",
                               "+ Nuevo Proveedor", self._nuevo, solo_admin=True)
        hdr.pack(fill="x")

        # Filtros
        fil = ctk.CTkFrame(self, fg_color="#21262d", height=52, corner_radius=0)
        fil.pack(fill="x")
        fil.pack_propagate(False)

        self._search_var = tk.StringVar()
        ctk.CTkEntry(fil, textvariable=self._search_var,
                     placeholder_text="Buscar proveedor…",
                     width=260, height=32).pack(side="left", padx=10, pady=10)

        self._activo_var = tk.StringVar(value="activos")
        ctk.CTkComboBox(fil, variable=self._activo_var,
                        values=["activos", "inactivos", "todos"],
                        width=120, height=32, state="readonly").pack(side="left", padx=4)

        ctk.CTkButton(fil, text="Buscar", command=self.refresh,
                      width=80, height=32,
                      fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER).pack(side="left", padx=4)

        # Tabla
        cols = [
            ("nombre",   "Nombre",    220),
            ("email",    "Email",     180),
            ("telefono", "Teléfono",  120),
            ("productos","Productos",  90, "e"),
            ("pedidos",  "Pedidos",    80, "e"),
            ("estado",   "Estado",     80),
        ]
        tframe, self.tree = self.make_table(self, cols)
        tframe.pack(fill="both", expand=True, padx=10, pady=6)
        self.tree.bind("<Double-1>", lambda _: self._ver_detalle())

        bar = ctk.CTkFrame(self, fg_color="transparent", height=44)
        bar.pack(fill="x", padx=10, pady=(0, 6))
        bar.pack_propagate(False)

        ctk.CTkButton(bar, text="Ver detalle", command=self._ver_detalle,
                      width=120, height=32).pack(side="left", padx=4)
        if self.current_user.es_admin:
            ctk.CTkButton(bar, text="Editar", command=self._editar,
                          fg_color="#374151", hover_color="#4b5563",
                          width=90, height=32).pack(side="left", padx=4)
            ctk.CTkButton(bar, text="Desactivar", command=self._desactivar,
                          fg_color="#7f1d1d", hover_color="#991b1b",
                          width=100, height=32).pack(side="left", padx=4)

    def refresh(self):
        from database import Proveedor, Producto, Pedido

        for row in self.tree.get_children():
            self.tree.delete(row)

        search = self._search_var.get().strip().lower()
        filtro = self._activo_var.get()

        try:
            with self.get_session() as s:
                q = s.query(Proveedor)
                if filtro == "activos":
                    q = q.filter(Proveedor.activo == True)
                elif filtro == "inactivos":
                    q = q.filter(Proveedor.activo == False)
                provs = q.order_by(Proveedor.nombre).all()

                for p in provs:
                    if search and search not in p.nombre.lower():
                        continue
                    n_prod = len(p.productos)
                    n_ped  = len(p.pedidos)
                    estado = "Activo" if p.activo else "Inactivo"
                    self.tree.insert("", "end", iid=str(p.id), values=(
                        p.nombre, p.email or "—",
                        p.telefono or "—",
                        n_prod, n_ped, estado,
                    ), tags=() if p.activo else ("inactivo",))
        except Exception as exc:
            self.show_error(str(exc))

        self.tree.tag_configure("inactivo", foreground="#6b7280")

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            self.show_error("Selecciona un proveedor primero.")
            return None
        return int(sel[0])

    def _ver_detalle(self):
        pid = self._selected_id()
        if pid:
            DetalleProveedorModal(self, pid)

    def _nuevo(self):
        m = ProveedorFormModal(self, None)
        self.wait_window(m)
        self.refresh()

    def _editar(self):
        pid = self._selected_id()
        if pid:
            m = ProveedorFormModal(self, pid)
            self.wait_window(m)
            self.refresh()

    def _desactivar(self):
        pid = self._selected_id()
        if not pid:
            return
        if not self.confirm("¿Desactivar este proveedor?"):
            return
        try:
            with self.get_session() as s:
                p = s.query(__import__("database", fromlist=["Proveedor"]).Proveedor).get(pid)
                if p:
                    p.activo = False
                    s.commit()
            self.refresh()
        except Exception as exc:
            self.show_error(str(exc))


# ─────────────────────────────────────────────────────────
#  MODAL DETALLE
# ─────────────────────────────────────────────────────────

class DetalleProveedorModal(ModalBase):
    def __init__(self, parent, prov_id: int):
        super().__init__(parent, "Detalle Proveedor", ancho=600, alto=460)
        self._load(prov_id)
        ctk.CTkButton(self.btn_bar, text="Cerrar", command=self.destroy,
                      fg_color="#374151", hover_color="#4b5563",
                      width=100).pack(side="right")

    def _load(self, pid):
        from database import Proveedor, Pedido, get_session
        from utils.helpers import fmt_fecha

        with get_session() as s:
            p = s.query(Proveedor).get(pid)
            if not p:
                return

            info = [
                ("Nombre",    p.nombre),
                ("Email",     p.email or "—"),
                ("Teléfono",  p.telefono or "—"),
                ("Dirección", p.direccion or "—"),
                ("Estado",    "Activo" if p.activo else "Inactivo"),
                ("Registrado", fmt_fecha(p.creado_en)),
            ]
            for i, (lbl, val) in enumerate(info):
                ctk.CTkLabel(self.content, text=f"{lbl}:", text_color="#9ca3af",
                             font=ctk.CTkFont(size=11), anchor="e").grid(
                    row=i, column=0, sticky="e", padx=(4, 8), pady=3)
                ctk.CTkLabel(self.content, text=val, text_color="white",
                             font=ctk.CTkFont(size=12), anchor="w",
                             wraplength=400).grid(
                    row=i, column=1, sticky="w", padx=4, pady=3)
            self.content.grid_columnconfigure(1, weight=1)

            # Últimos pedidos
            sep = len(info)
            ctk.CTkLabel(self.content, text="Últimos pedidos",
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color="white").grid(
                row=sep, column=0, columnspan=2, sticky="w", padx=4, pady=(12, 4))

            ultimos = (s.query(Pedido)
                       .filter_by(proveedor_id=pid)
                       .order_by(Pedido.fecha_pedido.desc())
                       .limit(5).all())
            if ultimos:
                from tkinter import ttk
                from views.base_view import apply_treeview_style
                apply_treeview_style()
                tf = ctk.CTkFrame(self.content, fg_color="#1c1c1c")
                tf.grid(row=sep+1, column=0, columnspan=2, sticky="ew", padx=4)
                t = ttk.Treeview(tf, columns=("num","estado","fecha"),
                                 show="headings", style="LabTrack.Treeview", height=5)
                for cid, ctxt, cw in [("num","Número",130),("estado","Estado",90),("fecha","Fecha",120)]:
                    t.heading(cid, text=ctxt); t.column(cid, width=cw)
                for ped in ultimos:
                    t.insert("", "end", values=(ped.numero, ped.estado,
                                                fmt_fecha(ped.fecha_pedido)))
                t.pack(fill="x")
            else:
                ctk.CTkLabel(self.content, text="Sin pedidos registrados.",
                             text_color="#6b7280").grid(
                    row=sep+1, column=0, columnspan=2, sticky="w", padx=4)


# ─────────────────────────────────────────────────────────
#  MODAL FORMULARIO
# ─────────────────────────────────────────────────────────

class ProveedorFormModal(ModalBase):
    def __init__(self, parent, prov_id):
        titulo = "Nuevo Proveedor" if prov_id is None else "Editar Proveedor"
        super().__init__(parent, titulo, ancho=480, alto=460)
        self._pid = prov_id
        self._build_form()
        if prov_id:
            self._load()
        self.add_buttons(self._guardar)

    def _get_session(self):
        from database import get_session
        return get_session()

    def _build_form(self):
        r = 0
        self.add_label("Nombre *", r); r += 1
        self.e_nombre = self.add_entry(r, "Nombre del proveedor"); r += 1
        self.add_label("Email", r); r += 1
        self.e_email = self.add_entry(r, "proveedor@empresa.com"); r += 1
        self.add_label("Teléfono", r); r += 1
        self.e_tel = self.add_entry(r, "+34 900 000 000"); r += 1
        self.add_label("Dirección", r); r += 1
        self.e_dir = self.add_textbox(r, height=70); r += 1

    def _load(self):
        from database import Proveedor
        with self._get_session() as s:
            p = s.query(Proveedor).get(self._pid)
            if not p:
                return
            self.e_nombre.insert(0, p.nombre)
            if p.email:    self.e_email.insert(0, p.email)
            if p.telefono: self.e_tel.insert(0, p.telefono)
            self.set_tb(self.e_dir, p.direccion or "")

    def _guardar(self):
        from database import Proveedor
        nombre = self.e_nombre.get().strip()
        if not nombre:
            self.show_error("El nombre es obligatorio.")
            return

        with self._get_session() as s:
            if self._pid is None:
                p = Proveedor()
                s.add(p)
            else:
                p = s.query(Proveedor).get(self._pid)

            p.nombre    = nombre
            p.email     = self.e_email.get().strip() or None
            p.telefono  = self.e_tel.get().strip() or None
            p.direccion = self.get_tb(self.e_dir) or None
            s.commit()

        self.destroy()

    def show_error(self, msg):
        from tkinter import messagebox
        messagebox.showerror("Error", msg, parent=self)
