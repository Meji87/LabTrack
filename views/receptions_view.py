"""
receptions_view.py — Recepciones de pedidos con adjunto de PDFs
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog
import customtkinter as ctk

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from views.base_view import BaseView, ModalBase, apply_treeview_style
from config import COLOR_ACCENT, COLOR_ACCENT_HOVER


class RecepcionesView(BaseView):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        apply_treeview_style()
        self._build()
        self.refresh()

    def _build(self):
        hdr = self.make_header(self, "Recepciones",
                               "+ Nueva Recepción", self._nueva)
        hdr.pack(fill="x")

        cols = [
            ("pedido",    "Nº Pedido",   130),
            ("proveedor", "Proveedor",   190),
            ("fecha",     "Fecha",        120),
            ("albaran",   "Albarán",      110),
            ("factura",   "Factura",      110),
            ("recibido",  "Recibido por", 130),
        ]
        tframe, self.tree = self.make_sortable_table(self, cols)
        tframe.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", lambda _: self._ver_detalle())

        bar = ctk.CTkFrame(self, fg_color="transparent", height=44)
        bar.pack(fill="x", padx=10, pady=(0, 6))
        bar.pack_propagate(False)

        ctk.CTkButton(bar, text="Ver detalle", command=self._ver_detalle,
                      width=120, height=32).pack(side="left", padx=4)
        ctk.CTkButton(bar, text="📄 Abrir albarán", command=self._abrir_albaran,
                      fg_color="#1e3a5f", hover_color="#1e40af",
                      width=130, height=32).pack(side="left", padx=4)
        ctk.CTkButton(bar, text="📄 Abrir factura", command=self._abrir_factura,
                      fg_color="#1e3a5f", hover_color="#1e40af",
                      width=130, height=32).pack(side="left", padx=4)

    def refresh(self):
        from database import Recepcion
        from utils.helpers import fmt_fecha

        for row in self.tree.get_children():
            self.tree.delete(row)

        try:
            with self.get_session() as s:
                recepciones = (s.query(Recepcion)
                               .order_by(Recepcion.fecha_recepcion.desc())
                               .all())
                for r in recepciones:
                    self.tree.insert("", "end", iid=str(r.id), values=(
                        r.pedido.numero if r.pedido else "—",
                        r.pedido.proveedor.nombre if r.pedido and r.pedido.proveedor else "—",
                        fmt_fecha(r.fecha_recepcion),
                        r.numero_albaran or "—",
                        r.numero_factura or "—",
                        r.recibido_por.nombre if r.recibido_por else "—",
                    ))
        except Exception as exc:
            self.show_error(str(exc))

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            self.show_error("Selecciona una recepción primero.")
            return None
        return int(sel[0])

    def _ver_detalle(self):
        rid = self._selected_id()
        if rid:
            DetalleRecepcionModal(self, rid)

    def _nueva(self):
        m = NuevaRecepcionModal(self, self.current_user, self.get_session)
        self.wait_window(m)
        self.refresh()

    def _abrir_pdf_de(self, campo):
        rid = self._selected_id()
        if not rid:
            return
        from database import Recepcion
        from utils.helpers import abrir_pdf
        try:
            with self.get_session() as s:
                r = s.query(Recepcion).get(rid)
                ruta = getattr(r, campo, None)
            if not abrir_pdf(ruta):
                self.show_error("No se encontró el archivo PDF.")
        except Exception as exc:
            self.show_error(str(exc))

    def _abrir_albaran(self):
        self._abrir_pdf_de("archivo_albaran")

    def _abrir_factura(self):
        self._abrir_pdf_de("archivo_factura")


# ─────────────────────────────────────────────────────────
#  MODAL DETALLE
# ─────────────────────────────────────────────────────────

class DetalleRecepcionModal(ModalBase):
    def __init__(self, parent, rec_id: int):
        super().__init__(parent, "Detalle Recepción", ancho=620, alto=440)
        self._load(rec_id)
        ctk.CTkButton(self.btn_bar, text="Cerrar", command=self.destroy,
                      fg_color="#374151", hover_color="#4b5563",
                      width=100).pack(side="right")

    def _load(self, rid):
        from database import Recepcion, get_session
        from utils.helpers import fmt_fecha

        with get_session() as s:
            r = s.query(Recepcion).get(rid)
            if not r:
                return

            info = [
                ("Pedido",        r.pedido.numero if r.pedido else "—"),
                ("Proveedor",     r.pedido.proveedor.nombre if r.pedido and r.pedido.proveedor else "—"),
                ("Fecha",         fmt_fecha(r.fecha_recepcion)),
                ("Nº Albarán",    r.numero_albaran or "—"),
                ("Nº Factura",    r.numero_factura or "—"),
                ("Archivo albarán", r.archivo_albaran or "—"),
                ("Archivo factura", r.archivo_factura or "—"),
                ("Recibido por",  r.recibido_por.nombre if r.recibido_por else "—"),
                ("Notas",         r.notas or "—"),
            ]
            for i, (lbl, val) in enumerate(info):
                ctk.CTkLabel(self.content, text=f"{lbl}:", text_color="#9ca3af",
                             font=ctk.CTkFont(size=11), anchor="e").grid(
                    row=i, column=0, sticky="e", padx=(4, 8), pady=3)
                ctk.CTkLabel(self.content, text=val, text_color="white",
                             font=ctk.CTkFont(size=12), anchor="w",
                             wraplength=380).grid(
                    row=i, column=1, sticky="w", padx=4, pady=3)
            self.content.grid_columnconfigure(1, weight=1)


# ─────────────────────────────────────────────────────────
#  MODAL NUEVA RECEPCIÓN
# ─────────────────────────────────────────────────────────

class NuevaRecepcionModal(ctk.CTkToplevel):
    """Modal para registrar la recepción de un pedido."""

    # Persistencia de última ruta usada para PDFs
    _last_pdf_dir: str = ""

    def __init__(self, parent, current_user, get_session_fn):
        super().__init__(parent)
        self.title("Nueva Recepción")
        self.geometry("700x700")
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()
        self._user = current_user
        self._get_session = get_session_fn
        self._albaran_path = ""
        self._factura_path = ""
        # Cantidades por línea de pedido: {linea_id: StringVar}
        self._cant_vars: dict[int, tk.StringVar] = {}
        self._lote_vars: dict[int, tk.StringVar] = {}
        self._cad_vars:  dict[int, tk.StringVar] = {}

        self.update_idletasks()
        x = (self.winfo_screenwidth() - 700) // 2
        y = (self.winfo_screenheight() - 700) // 2
        self.geometry(f"+{x}+{y}")

        self._build()
        self.after(200, self._set_icon)

    def _set_icon(self):
        import os
        app = self.master
        while app and not hasattr(app, '_ico_path'):
            app = getattr(app, 'master', None)
        if app and hasattr(app, '_ico_path') and os.path.isfile(app._ico_path):
            try:
                self.iconbitmap(app._ico_path)
            except Exception:
                pass

    def _build(self):
        from database import Pedido

        hdr = ctk.CTkFrame(self, height=46, fg_color="#111827", corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="Nueva Recepción",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color="white").pack(side="left", padx=16, pady=8)

        self.content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=16, pady=10)
        self.content.grid_columnconfigure(1, weight=1)

        r = 0

        # Selección de pedido
        ctk.CTkLabel(self.content, text="Pedido a recepcionar *",
                     text_color="#9ca3af", font=ctk.CTkFont(size=12), anchor="w").grid(
            row=r, column=0, columnspan=2, sticky="w", padx=4, pady=(4, 2)); r += 1

        with self._get_session() as s:
            pedidos_env = (s.query(Pedido)
                           .filter(Pedido.estado.in_(["enviado", "pendiente", "borrador"]))
                           .order_by(Pedido.fecha_pedido.desc())
                           .all())
            self._ped_map = {f"{p.numero} — {p.proveedor.nombre}": p.id for p in pedidos_env}

        ped_list = list(self._ped_map.keys())
        self._ped_var = tk.StringVar()
        self._ped_cb = ctk.CTkComboBox(
            self.content, variable=self._ped_var,
            values=ped_list if ped_list else ["(Sin pedidos pendientes)"],
            width=380, height=32, state="readonly",
            command=self._on_pedido_change,
        )
        self._ped_cb.grid(row=r, column=0, columnspan=2, sticky="w", padx=4, pady=(0, 8)); r += 1

        # Fecha de recepción
        from datetime import datetime as _dt
        ctk.CTkLabel(self.content, text="Fecha de recepción",
                     text_color="#9ca3af", font=ctk.CTkFont(size=12), anchor="w").grid(
            row=r, column=0, columnspan=2, sticky="w", padx=4, pady=(4, 2)); r += 1
        self._fecha_rec_var = tk.StringVar(value=_dt.now().strftime("%d/%m/%Y"))
        fecha_entry = ctk.CTkEntry(self.content, textvariable=self._fecha_rec_var,
                                   width=140, height=32)
        fecha_entry.grid(row=r, column=0, columnspan=2, sticky="w", padx=4, pady=(0, 8)); r += 1
        fecha_entry.bind("<Button-1>",
                         lambda e: self._abrir_calendario(self._fecha_rec_var, fecha_entry))

        # Campos de recepción
        for lbl, attr in [("Nº Albarán", "_alb_entry"), ("Nº Factura", "_fac_entry")]:
            ctk.CTkLabel(self.content, text=lbl,
                         text_color="#9ca3af", font=ctk.CTkFont(size=12), anchor="w").grid(
                row=r, column=0, columnspan=2, sticky="w", padx=4, pady=(4, 2)); r += 1
            entry = ctk.CTkEntry(self.content, height=32)
            entry.grid(row=r, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 6)); r += 1
            setattr(self, attr, entry)

        # PDFs
        ctk.CTkLabel(self.content, text="PDF Albarán",
                     text_color="#9ca3af", font=ctk.CTkFont(size=12)).grid(
            row=r, column=0, columnspan=2, sticky="w", padx=4, pady=(4, 2)); r += 1
        pdf_row1 = ctk.CTkFrame(self.content, fg_color="transparent")
        pdf_row1.grid(row=r, column=0, columnspan=2, sticky="ew", padx=4); r += 1
        self._alb_path_lbl = ctk.CTkLabel(pdf_row1, text="Sin archivo",
                                           text_color="#6b7280", anchor="w")
        self._alb_path_lbl.pack(side="left", expand=True, fill="x")
        ctk.CTkButton(pdf_row1, text="Seleccionar PDF", width=140, height=30,
                      command=self._sel_albaran).pack(side="right")

        ctk.CTkLabel(self.content, text="PDF Factura",
                     text_color="#9ca3af", font=ctk.CTkFont(size=12)).grid(
            row=r, column=0, columnspan=2, sticky="w", padx=4, pady=(8, 2)); r += 1
        pdf_row2 = ctk.CTkFrame(self.content, fg_color="transparent")
        pdf_row2.grid(row=r, column=0, columnspan=2, sticky="ew", padx=4); r += 1
        self._fac_path_lbl = ctk.CTkLabel(pdf_row2, text="Sin archivo",
                                           text_color="#6b7280", anchor="w")
        self._fac_path_lbl.pack(side="left", expand=True, fill="x")
        ctk.CTkButton(pdf_row2, text="Seleccionar PDF", width=140, height=30,
                      command=self._sel_factura).pack(side="right")

        # Cantidades recibidas (se llena al seleccionar pedido)
        ctk.CTkLabel(self.content, text="Cantidades recibidas",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="white").grid(
            row=r, column=0, columnspan=2, sticky="w", padx=4, pady=(14, 4)); r += 1
        self._lineas_frame = ctk.CTkFrame(self.content, fg_color="#21262d", corner_radius=6)
        self._lineas_frame.grid(row=r, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 8)); r += 1
        self._lineas_start_row = r

        ctk.CTkLabel(self.content, text="Notas",
                     text_color="#9ca3af", font=ctk.CTkFont(size=12)).grid(
            row=r, column=0, columnspan=2, sticky="w", padx=4, pady=(4, 2)); r += 1
        self._notas_tb = ctk.CTkTextbox(self.content, height=60)
        self._notas_tb.grid(row=r, column=0, columnspan=2, sticky="ew", padx=4); r += 1

        self._email_var = tk.BooleanVar()
        ctk.CTkCheckBox(self.content, text="Enviar email de confirmación al proveedor",
                        variable=self._email_var).grid(
            row=r, column=0, columnspan=2, sticky="w", padx=4, pady=8); r += 1

        # Botones
        btn_bar = ctk.CTkFrame(self, height=52, fg_color="transparent")
        btn_bar.pack(fill="x", padx=16, pady=(0, 12))
        btn_bar.pack_propagate(False)
        ctk.CTkButton(btn_bar, text="Cancelar", command=self.destroy,
                      fg_color="#374151", hover_color="#4b5563",
                      width=100, height=34).pack(side="right", padx=4)
        ctk.CTkButton(btn_bar, text="Guardar Recepción", command=self._guardar,
                      fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
                      width=160, height=34).pack(side="right", padx=4)
        
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

    def _on_pedido_change(self, choice):
        from database import Pedido

        for w in self._lineas_frame.winfo_children():
            w.destroy()
        self._cant_vars.clear()
        self._lote_vars.clear()
        self._cad_vars.clear()

        ped_id = self._ped_map.get(choice)
        if not ped_id:
            return

        with self._get_session() as s:
            ped = s.query(Pedido).get(ped_id)
            if not ped:
                return

            for linea in ped.lineas:
                # Tarjeta por línea
                card = ctk.CTkFrame(self._lineas_frame, fg_color="#2d333b", corner_radius=6)
                card.pack(fill="x", padx=6, pady=4)

                # Fila 1 — info del producto
                fila1 = ctk.CTkFrame(card, fg_color="transparent")
                fila1.pack(fill="x", padx=8, pady=(6, 2))

                ctk.CTkLabel(fila1, text=linea.producto.nombre,
                            font=ctk.CTkFont(size=12, weight="bold"),
                            text_color="white", anchor="w").pack(side="left")
                ctk.CTkLabel(fila1, text=f"  [{linea.producto.referencia}]",
                            font=ctk.CTkFont(size=11),
                            text_color="#9ca3af", anchor="w").pack(side="left")
                ctk.CTkLabel(fila1,
                            text=f"Pedido: {int(linea.cantidad_pedida) if linea.cantidad_pedida == int(linea.cantidad_pedida) else linea.cantidad_pedida} {linea.producto.unidad}",
                            font=ctk.CTkFont(size=11),
                            text_color="#9ca3af", anchor="e").pack(side="right")

                # Fila 2 — campos de entrada
                fila2 = ctk.CTkFrame(card, fg_color="transparent")
                fila2.pack(fill="x", padx=8, pady=(2, 8))

                # Cantidad recibida
                ctk.CTkLabel(fila2, text="Cant. recibida:",
                            font=ctk.CTkFont(size=11), text_color="#9ca3af").pack(side="left")
                v = tk.StringVar(value=str(
                    int(linea.cantidad_pedida) if linea.cantidad_pedida == int(linea.cantidad_pedida)
                    else linea.cantidad_pedida
                ))
                self._cant_vars[linea.id] = v
                ctk.CTkEntry(fila2, textvariable=v, width=70, height=28).pack(side="left", padx=(4, 12))
                ctk.CTkLabel(fila2, text=linea.producto.unidad,
                            font=ctk.CTkFont(size=11), text_color="#9ca3af").pack(side="left", padx=(0, 16))

                # Lote (si aplica)
                if linea.producto.tiene_lote:
                    ctk.CTkLabel(fila2, text="Nº lote:",
                                font=ctk.CTkFont(size=11), text_color="#9ca3af").pack(side="left")
                    lote_v = tk.StringVar()
                    ctk.CTkEntry(fila2, textvariable=lote_v, width=130, height=28,
                                placeholder_text="Número de lote").pack(side="left", padx=(4, 16))
                    self._lote_vars[linea.id] = lote_v

                # Caducidad (si aplica)
                if linea.producto.tiene_caducidad:
                    ctk.CTkLabel(fila2, text="Caducidad:",
                                font=ctk.CTkFont(size=11), text_color="#9ca3af").pack(side="left")
                    cad_v = tk.StringVar()
                    cad_entry = ctk.CTkEntry(fila2, textvariable=cad_v, width=100, height=28,
                                            placeholder_text="DD/MM/AAAA")
                    cad_entry.pack(side="left", padx=(4, 0))
                    cad_entry.bind("<Button-1>",
                                lambda e, v=cad_v, w=cad_entry: self._abrir_calendario(v, w))
                    self._cad_vars[linea.id] = cad_v

    def _sel_pdf(self, attr_path, lbl_widget):
        init_dir = NuevaRecepcionModal._last_pdf_dir or os.path.expanduser("~")
        path = filedialog.askopenfilename(
            parent=self,
            title="Seleccionar PDF",
            initialdir=init_dir,
            filetypes=[("PDF", "*.pdf *.PDF"), ("Todos", "*.*")],
        )
        if path:
            NuevaRecepcionModal._last_pdf_dir = os.path.dirname(path)
            setattr(self, attr_path, path)
            lbl_widget.configure(text=os.path.basename(path), text_color="white")

    def _sel_albaran(self):
        self._sel_pdf("_albaran_path", self._alb_path_lbl)

    def _sel_factura(self):
        self._sel_pdf("_factura_path", self._fac_path_lbl)

    def _guardar(self):
        from database import Pedido, Recepcion, MovimientoStock, Producto
        from utils.helpers import guardar_documento
        from utils.email_utils import enviar_confirmacion_recepcion
        from datetime import datetime
        from tkinter import messagebox

        ped_choice = self._ped_var.get()
        if not ped_choice or ped_choice == "(Sin pedidos pendientes)":
            messagebox.showerror("Error", "Selecciona un pedido.", parent=self)
            return

        ped_id = self._ped_map.get(ped_choice)

        with self._get_session() as s:
            ped = s.query(Pedido).get(ped_id)
            if not ped:
                return

            # Guardar PDFs
            alb_num  = self._alb_entry.get().strip() or "albaran"
            fac_num  = self._fac_entry.get().strip() or "factura"
            ruta_alb = guardar_documento(self._albaran_path, "albaran", alb_num) if self._albaran_path else None
            ruta_fac = guardar_documento(self._factura_path, "factura", fac_num) if self._factura_path else None

            from utils.helpers import parse_fecha
            fecha_rec = parse_fecha(self._fecha_rec_var.get())
            from datetime import datetime as _dtutil
            fecha_rec_dt = _dtutil.combine(fecha_rec, _dtutil.min.time()) if fecha_rec else _dtutil.utcnow()

            rec = Recepcion(
                pedido_id=ped_id,
                fecha_recepcion=fecha_rec_dt,
                numero_albaran=self._alb_entry.get().strip() or None,
                numero_factura=self._fac_entry.get().strip() or None,
                archivo_albaran=ruta_alb,
                archivo_factura=ruta_fac,
                notas=self._notas_tb.get("1.0", "end").strip() or None,
                recibido_por_id=self._user.id if self._user else None,
            )
            s.add(rec)

            # Actualizar stock y registrar movimientos
            for linea in ped.lineas:
                var = self._cant_vars.get(linea.id)
                if not var:
                    continue
                try:
                    cant_recib = float(var.get() or "0")
                except ValueError:
                    cant_recib = 0
                if cant_recib <= 0:
                    continue

                prod = s.query(Producto).get(linea.producto_id)
                if not prod:
                    continue

                antes = prod.cantidad_actual
                prod.cantidad_actual += cant_recib

                # Crear lote si corresponde
                from database import LoteProducto
                from utils.helpers import parse_fecha

                if prod.tiene_lote or prod.tiene_caducidad:
                    numero_lote = self._lote_vars.get(linea.id)
                    fecha_cad_v = self._cad_vars.get(linea.id)
                    lote = LoteProducto(
                        producto_id=prod.id,
                        numero_lote=numero_lote.get().strip() if numero_lote else None,
                        fecha_caducidad=parse_fecha(fecha_cad_v.get()) if fecha_cad_v else None,
                        cantidad=cant_recib,
                    )
                    s.add(lote)
                    # Asignar recepcion_id después del flush

                s.add(MovimientoStock(
                    producto_id=prod.id,
                    usuario_id=self._user.id if self._user else None,
                    tipo="recepcion",
                    cantidad=cant_recib,
                    cantidad_anterior=antes,
                    cantidad_posterior=prod.cantidad_actual,
                    motivo=f"Recepción pedido {ped.numero}",
                    referencia_doc=self._alb_entry.get().strip() or ped.numero,
                ))

            # Recepción parcial: solo marcar como recibido si todas las líneas tienen cantidad completa
            all_received = True
            for linea in ped.lineas:
                var = self._cant_vars.get(linea.id)
                try:
                    cant_recib = float(var.get() or "0") if var else 0.0
                except ValueError:
                    cant_recib = 0.0
                if cant_recib < linea.cantidad_pedida:
                    all_received = False
                    break
            ped.estado = "recibido" if all_received else "pendiente"
            s.flush()

            # Asignar recepcion_id a los lotes recién creados
            for lote in rec.lotes:
                lote.recepcion_id = rec.id

            # Email de confirmación opcional
            if self._email_var.get():
                ok, msg = enviar_confirmacion_recepcion(rec)
                if not ok:
                    messagebox.showwarning("Email", f"Recepción guardada, pero no se pudo enviar email:\n{msg}", parent=self)

            s.commit()

        self.destroy()
