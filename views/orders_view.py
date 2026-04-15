"""
orders_view.py — Gestión de pedidos (crear, ver, enviar por email, cancelar)
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
from config import COLOR_ACCENT, COLOR_ACCENT_HOVER, COLOR_DANGER, COLOR_WARNING, COLOR_SUCCESS


_ESTADO_COLORS = {
    "borrador":  "#374151",
    "pendiente": "#78350f",
    "enviado":   "#1e3a5f",
    "recibido":  "#14532d",
    "cancelado": "#3d1515",
}


class PedidosView(BaseView):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        apply_treeview_style()
        self._build()
        self.refresh()

    def _build(self):
        hdr = self.make_header(self, "Pedidos", "+ Nuevo Pedido", self._nuevo)
        hdr.pack(fill="x")

        fil = ctk.CTkFrame(self, fg_color="#21262d", height=52, corner_radius=0)
        fil.pack(fill="x")
        fil.pack_propagate(False)

        self._estado_var = tk.StringVar(value="todos")
        ctk.CTkComboBox(
            fil, variable=self._estado_var,
            values=["todos", "borrador", "pendiente", "enviado", "recibido", "cancelado"],
            width=140, height=32, state="readonly",
        ).pack(side="left", padx=10, pady=10)

        ctk.CTkButton(fil, text="Filtrar", command=self.refresh,
                      width=80, height=32,
                      fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER).pack(side="left", padx=4)

        cols = [
            ("numero",    "Número",     140),
            ("proveedor", "Proveedor",  200),
            ("estado",    "Estado",      90),
            ("lineas",    "Líneas",       70, "e"),
            ("fecha",     "Fecha",       120),
            ("creado",    "Creado por",  120),
        ]
        tframe, self.tree = self.make_sortable_table(self, cols)
        tframe.pack(fill="both", expand=True, padx=10, pady=6)
        self.tree.bind("<Double-1>", lambda _: self._ver_detalle())

        bar = ctk.CTkFrame(self, fg_color="transparent", height=44)
        bar.pack(fill="x", padx=10, pady=(0, 6))
        bar.pack_propagate(False)

        ctk.CTkButton(bar, text="Ver detalle", command=self._ver_detalle,
                      width=120, height=32).pack(side="left", padx=4)
        ctk.CTkButton(bar, text="📧 Enviar email", command=self._enviar_email,
                      fg_color="#1e3a5f", hover_color="#1e40af",
                      width=130, height=32).pack(side="left", padx=4)
        ctk.CTkButton(bar, text="Cancelar pedido", command=self._cancelar,
                      fg_color="#7f1d1d", hover_color="#991b1b",
                      width=120, height=32).pack(side="left", padx=4)

    def refresh(self):
        from database import Pedido
        from utils.helpers import fmt_fecha

        for row in self.tree.get_children():
            self.tree.delete(row)

        estado_fil = self._estado_var.get()

        try:
            with self.get_session() as s:
                q = s.query(Pedido)
                if estado_fil != "todos":
                    q = q.filter(Pedido.estado == estado_fil)
                pedidos = q.order_by(Pedido.fecha_pedido.desc()).all()

                for p in pedidos:
                    tag = p.estado
                    self.tree.insert("", "end", iid=str(p.id), values=(
                        p.numero,
                        p.proveedor.nombre if p.proveedor else "—",
                        p.estado,
                        len(p.lineas),
                        fmt_fecha(p.fecha_pedido),
                        p.creado_por.nombre if p.creado_por else "—",
                    ), tags=(tag,))

        except Exception as exc:
            self.show_error(str(exc))

        for estado, bg in _ESTADO_COLORS.items():
            self.tree.tag_configure(estado, background=bg)

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            self.show_error("Selecciona un pedido primero.")
            return None
        return int(sel[0])

    def _ver_detalle(self):
        pid = self._selected_id()
        if pid:
            DetallePedidoModal(self, pid)

    def _nuevo(self):
        m = NuevoPedidoModal(self, self.current_user, self.get_session)
        self.wait_window(m)
        self.refresh()

    def _enviar_email(self):
        pid = self._selected_id()
        if not pid:
            return
        from database import Pedido
        from utils.email_utils import enviar_pedido_proveedor
        from datetime import datetime

        try:
            with self.get_session() as s:
                p = s.query(Pedido).get(pid)
                if not p:
                    return
                if p.estado == "recibido":
                    self.show_error("El pedido ya fue recibido.")
                    return
                if p.estado == "cancelado":
                    self.show_error("El pedido está cancelado.")
                    return
                if not p.lineas:
                    self.show_error("El pedido no tiene líneas de productos.")
                    return

                ok, msg = enviar_pedido_proveedor(p)
                if ok:
                    p.estado     = "enviado"
                    p.fecha_envio = datetime.utcnow()
                    s.commit()
                    self.show_info(msg)
                else:
                    self.show_error(msg)
        except Exception as exc:
            self.show_error(str(exc))

        self.refresh()

    def _cancelar(self):
        pid = self._selected_id()
        if not pid:
            return
        from database import Pedido

        if not self.confirm("¿Cancelar este pedido?"):
            return
        try:
            with self.get_session() as s:
                p = s.query(Pedido).get(pid)
                if not p:
                    return
                if p.estado == "recibido":
                    self.show_error("No se puede cancelar un pedido ya recibido.")
                    return
                p.estado = "cancelado"
                s.commit()
            self.refresh()
        except Exception as exc:
            self.show_error(str(exc))


# ─────────────────────────────────────────────────────────
#  MODAL DETALLE PEDIDO
# ─────────────────────────────────────────────────────────

class DetallePedidoModal(ModalBase):
    def __init__(self, parent, pedido_id: int):
        super().__init__(parent, "Detalle de Pedido", ancho=700, alto=520)
        self._load(pedido_id)
        ctk.CTkButton(self.btn_bar, text="Cerrar", command=self.destroy,
                      fg_color="#374151", hover_color="#4b5563",
                      width=100).pack(side="right")

    def _load(self, pid):
        from database import Pedido, get_session
        from utils.helpers import fmt_fecha

        with get_session() as s:
            p = s.query(Pedido).get(pid)
            if not p:
                return

            info = [
                ("Número",    p.numero),
                ("Proveedor", p.proveedor.nombre if p.proveedor else "—"),
                ("Estado",    p.estado),
                ("Fecha",     fmt_fecha(p.fecha_pedido)),
                ("Enviado",   fmt_fecha(p.fecha_envio) if p.fecha_envio else "—"),
                ("Creado por",p.creado_por.nombre if p.creado_por else "—"),
                ("Notas",     p.notas or "—"),
            ]
            for i, (lbl, val) in enumerate(info):
                ctk.CTkLabel(self.content, text=f"{lbl}:", text_color="#9ca3af",
                             font=ctk.CTkFont(size=11), anchor="e").grid(
                    row=i, column=0, sticky="e", padx=(4, 8), pady=2)
                ctk.CTkLabel(self.content, text=val, text_color="white",
                             font=ctk.CTkFont(size=12), anchor="w",
                             wraplength=480).grid(
                    row=i, column=1, sticky="w", padx=4, pady=2)
            self.content.grid_columnconfigure(1, weight=1)

            sep = len(info)
            ctk.CTkLabel(self.content, text="Líneas del pedido",
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color="white").grid(
                row=sep, column=0, columnspan=2, sticky="w", padx=4, pady=(12, 4))

            apply_treeview_style()
            tf = ctk.CTkFrame(self.content, fg_color="#1c1c1c")
            tf.grid(row=sep+1, column=0, columnspan=2, sticky="ew", padx=4)
            t = ttk.Treeview(
                tf, columns=("prod","ref","cant","precio","notas"),
                show="headings", style="LabTrack.Treeview", height=6,
            )
            for cid, ctxt, cw in [
                ("prod","Producto",200),("ref","Ref.",120),
                ("cant","Cantidad",80),("precio","Precio",80),("notas","Notas",180),
            ]:
                t.heading(cid, text=ctxt); t.column(cid, width=cw)

            for l in p.lineas:
                precio = f"{l.precio_unitario:.2f} €" if l.precio_unitario else "—"
                t.insert("", "end", values=(
                    l.producto.nombre, l.producto.referencia,
                    f"{l.cantidad_pedida} {l.producto.unidad}",
                    precio, l.notas or "—",
                ))

            vsb = ttk.Scrollbar(tf, orient="vertical", command=t.yview,
                                style="LabTrack.Vertical.TScrollbar")
            t.configure(yscrollcommand=vsb.set)
            t.grid(row=0, column=0, sticky="nsew"); vsb.grid(row=0, column=1, sticky="ns")
            tf.grid_rowconfigure(0, weight=1); tf.grid_columnconfigure(0, weight=1)


# ─────────────────────────────────────────────────────────
#  MODAL NUEVO PEDIDO
# ─────────────────────────────────────────────────────────

class NuevoPedidoModal(ctk.CTkToplevel):
    """Modal complejo para crear un pedido con líneas de productos."""

    def __init__(self, parent, current_user, get_session_fn):
        super().__init__(parent)
        self.title("Nuevo Pedido")
        self.geometry("820x620")
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()
        self._user = current_user
        self._get_session = get_session_fn
        self._lineas: list[dict] = []  # {"producto_id", "nombre", "referencia", "unidad", "cantidad", "precio", "notas"}

        self.update_idletasks()
        x = (self.winfo_screenwidth() - 820) // 2
        y = (self.winfo_screenheight() - 620) // 2
        self.geometry(f"+{x}+{y}")

        self._build()

    def _build(self):
        from database import Proveedor, Producto, get_session

        # Header
        hdr = ctk.CTkFrame(self, height=46, fg_color="#111827", corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="Nuevo Pedido",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color="white").pack(side="left", padx=16, pady=8)

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=16, pady=10)
        main.grid_columnconfigure(0, weight=1)

        # Fila proveedor + notas
        row0 = ctk.CTkFrame(main, fg_color="transparent")
        row0.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        row0.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(row0, text="Proveedor *", text_color="#9ca3af",
                     font=ctk.CTkFont(size=12)).grid(row=0, column=0, padx=(0, 8))
        with get_session() as s:
            provs = [p.nombre for p in s.query(Proveedor).filter_by(activo=True).order_by(Proveedor.nombre).all()]

        self._prov_var = tk.StringVar()
        self._prov_cb = ctk.CTkComboBox(row0, variable=self._prov_var,
                                         values=provs, width=220, height=32, state="readonly")
        self._prov_cb.grid(row=0, column=1, sticky="w", padx=(0, 16))

        ctk.CTkLabel(row0, text="Notas", text_color="#9ca3af",
                     font=ctk.CTkFont(size=12)).grid(row=0, column=2, padx=(0, 8))
        self._notas_entry = ctk.CTkEntry(row0, width=260, height=32, placeholder_text="Opcional")
        self._notas_entry.grid(row=0, column=3, sticky="ew")
        row0.grid_columnconfigure(3, weight=1)

        self._email_var = tk.BooleanVar()
        ctk.CTkCheckBox(row0, text="📧 Enviar email al proveedor al guardar",
                        variable=self._email_var).grid(
            row=1, column=0, columnspan=4, sticky="w", padx=(0, 8), pady=(6, 0))

        # Sección añadir producto
        sep1 = ctk.CTkFrame(main, fg_color="#21262d", corner_radius=8)
        sep1.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        ctk.CTkLabel(sep1, text="Añadir producto",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="white").pack(anchor="w", padx=10, pady=(8, 4))

        add_row = ctk.CTkFrame(sep1, fg_color="transparent")
        add_row.pack(fill="x", padx=10, pady=(0, 10))

        with get_session() as s:
            prods_raw = s.query(Producto).filter_by(estado="activo").order_by(Producto.nombre).all()
            self._prods_map = {f"{p.nombre} [{p.referencia}]": p.id for p in prods_raw}
            prods_list = list(self._prods_map.keys())

        self._prod_var = tk.StringVar()
        self._prod_cb = ctk.CTkComboBox(add_row, variable=self._prod_var,
                                         values=prods_list, width=260, height=32, state="readonly")
        self._prod_cb.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(add_row, text="Cant:", text_color="#9ca3af",
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 4))
        self._cant_entry = ctk.CTkEntry(add_row, width=70, height=32, placeholder_text="1")
        self._cant_entry.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(add_row, text="Notas línea:", text_color="#9ca3af",
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 4))
        self._nota_linea = ctk.CTkEntry(add_row, width=150, height=32)
        self._nota_linea.pack(side="left", padx=(0, 8))

        ctk.CTkButton(add_row, text="+ Añadir", command=self._add_linea,
                      fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
                      width=90, height=32).pack(side="left")

        # Tabla de líneas
        ctk.CTkLabel(main, text="Líneas del pedido",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="white").grid(row=2, column=0, sticky="w", pady=(4, 4))

        apply_treeview_style()
        tf = ctk.CTkFrame(main, fg_color="#1c1c1c", corner_radius=6)
        tf.grid(row=3, column=0, sticky="nsew", pady=(0, 8))
        main.grid_rowconfigure(3, weight=1)

        self._lines_tree = ttk.Treeview(
            tf,
            columns=("prod","ref","cant","precio","notas"),
            show="headings", style="LabTrack.Treeview", height=6,
        )
        for cid, ctxt, cw in [
            ("prod","Producto",220),("ref","Ref.",110),
            ("cant","Cantidad",80),("precio","Precio",80),("notas","Notas",180),
        ]:
            self._lines_tree.heading(cid, text=ctxt)
            self._lines_tree.column(cid, width=cw)

        vsb = ttk.Scrollbar(tf, orient="vertical", command=self._lines_tree.yview,
                            style="LabTrack.Vertical.TScrollbar")
        self._lines_tree.configure(yscrollcommand=vsb.set)
        self._lines_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        tf.grid_rowconfigure(0, weight=1); tf.grid_columnconfigure(0, weight=1)

        # Botones eliminar línea + guardar
        btn_bar = ctk.CTkFrame(main, fg_color="transparent", height=44)
        btn_bar.grid(row=4, column=0, sticky="ew")
        btn_bar.grid_propagate(False)

        ctk.CTkButton(btn_bar, text="Eliminar línea", command=self._del_linea,
                      fg_color="#7f1d1d", hover_color="#991b1b",
                      width=120, height=32).pack(side="left", padx=4)
        ctk.CTkButton(btn_bar, text="Cancelar", command=self.destroy,
                      fg_color="#374151", hover_color="#4b5563",
                      width=100, height=32).pack(side="right", padx=4)
        ctk.CTkButton(btn_bar, text="Guardar pedido", command=self._guardar,
                      fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
                      width=140, height=32).pack(side="right", padx=4)

    def _add_linea(self):
        from database import Producto, get_session
        nombre_clave = self._prod_var.get()
        if not nombre_clave:
            return

        prod_id = self._prods_map.get(nombre_clave)
        if not prod_id:
            return

        try:
            cant = float(self._cant_entry.get() or "1")
            if cant <= 0:
                raise ValueError
        except ValueError:
            from tkinter import messagebox
            messagebox.showerror("Error", "Cantidad debe ser número mayor que 0.", parent=self)
            return

        precio = None

        with get_session() as s:
            p = s.query(Producto).get(prod_id)
            if not p:
                return
            linea = {
                "producto_id": prod_id,
                "nombre": p.nombre,
                "referencia": p.referencia,
                "unidad": p.unidad,
                "cantidad": cant,
                "precio": precio,
                "notas": self._nota_linea.get().strip() or None,
            }

        self._lineas.append(linea)
        self._lines_tree.insert("", "end", values=(
            linea["nombre"], linea["referencia"],
            f"{cant} {linea['unidad']}",
            f"{precio:.2f} €" if precio else "—",
            linea["notas"] or "—",
        ))
        # Limpiar campos
        self._cant_entry.delete(0, "end")
        self._nota_linea.delete(0, "end")

    def _del_linea(self):
        sel = self._lines_tree.selection()
        if not sel:
            return
        idx = self._lines_tree.index(sel[0])
        self._lines_tree.delete(sel[0])
        del self._lineas[idx]

    def _guardar(self):
        from database import Pedido, LineaPedido, get_session
        from utils.helpers import generar_numero_pedido
        from database import Proveedor
        from datetime import datetime

        prov_nombre = self._prov_var.get()
        if not prov_nombre:
            from tkinter import messagebox
            messagebox.showerror("Error", "Selecciona un proveedor.", parent=self)
            return
        if not self._lineas:
            from tkinter import messagebox
            messagebox.showerror("Error", "Añade al menos una línea de producto.", parent=self)
            return

        pedido_id = None
        with self._get_session() as s:
            prov = s.query(Proveedor).filter_by(nombre=prov_nombre).first()
            if not prov:
                return

            numero = generar_numero_pedido(s)
            pedido = Pedido(
                numero=numero,
                proveedor_id=prov.id,
                notas=self._notas_entry.get().strip() or None,
                creado_por_id=self._user.id if self._user else None,
                estado="borrador",
                fecha_pedido=datetime.utcnow(),
            )
            s.add(pedido)
            s.flush()

            for l in self._lineas:
                s.add(LineaPedido(
                    pedido_id=pedido.id,
                    producto_id=l["producto_id"],
                    cantidad_pedida=l["cantidad"],
                    precio_unitario=None,
                    notas=l["notas"],
                ))

            pedido_id = pedido.id
            s.commit()

        # Enviar email si el checkbox está marcado
        if self._email_var.get() and pedido_id:
            try:
                from utils.email_utils import enviar_pedido_proveedor
                from database import Pedido as _Pedido
                with self._get_session() as s:
                    ped = s.query(_Pedido).get(pedido_id)
                    if ped:
                        ok, msg = enviar_pedido_proveedor(ped)
                        if ok:
                            ped.estado = "enviado"
                            ped.fecha_envio = datetime.utcnow()
                            s.commit()
            except Exception:
                pass

        self.destroy()
