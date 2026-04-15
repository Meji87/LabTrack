"""
admin_view.py — Gestión de usuarios, categorías, ubicaciones y unidades (solo admin)
"""

import os
import sys
import tkinter as tk
import customtkinter as ctk

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from views.base_view import BaseView, ModalBase, apply_treeview_style
from config import COLOR_ACCENT, COLOR_ACCENT_HOVER, COLOR_DANGER, COLOR_CARD_BG


class AdminView(BaseView):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        apply_treeview_style()
        self._build()
        self.refresh()

    def _build(self):
        hdr = self.make_header(self, "Administración")
        hdr.pack(fill="x")

        # Tabs
        tabs = ctk.CTkTabview(self)
        tabs.pack(fill="both", expand=True, padx=10, pady=8)

        tab_users  = tabs.add("Usuarios")
        tab_cats   = tabs.add("Categorías")
        tab_ubics  = tabs.add("Ubicaciones")
        tab_units  = tabs.add("Unidades")

        self._build_users(tab_users)
        self._build_cats(tab_cats)
        self._build_ubics(tab_ubics)
        self._build_units(tab_units)

    # ─────────────────────────────────────────────────────
    #  TAB USUARIOS
    # ─────────────────────────────────────────────────────

    def _build_users(self, parent):
        top = ctk.CTkFrame(parent, fg_color="transparent", height=44)
        top.pack(fill="x", pady=(4, 6))
        top.pack_propagate(False)
        ctk.CTkButton(top, text="+ Nuevo Usuario", command=self._nuevo_usuario,
                      fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
                      height=32, width=140).pack(side="left", padx=4)

        cols = [
            ("nombre",    "Nombre",    180),
            ("email",     "Email",     210),
            ("rol",       "Rol",        80),
            ("activo",    "Estado",     80),
            ("creado",    "Registrado", 130),
        ]
        tframe, self.user_tree = self.make_sortable_table(parent, cols)
        tframe.pack(fill="both", expand=True, pady=(0, 6))
        self.user_tree.bind("<Double-1>", lambda _: self._editar_usuario())

        bar = ctk.CTkFrame(parent, fg_color="transparent", height=44)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        ctk.CTkButton(bar, text="Editar", command=self._editar_usuario,
                      fg_color="#374151", hover_color="#4b5563",
                      width=90, height=32).pack(side="left", padx=4)
        ctk.CTkButton(bar, text="Desactivar / Activar", command=self._toggle_usuario,
                      fg_color="#78350f", hover_color="#92400e",
                      width=150, height=32).pack(side="left", padx=4)

    def _load_users(self):
        from database import Usuario
        from utils.helpers import fmt_fecha

        for row in self.user_tree.get_children():
            self.user_tree.delete(row)

        try:
            with self.get_session() as s:
                users = s.query(Usuario).order_by(Usuario.nombre).all()
                for u in users:
                    estado = "Activo" if u.activo else "Inactivo"
                    self.user_tree.insert("", "end", iid=str(u.id), values=(
                        u.nombre, u.email, u.rol,
                        estado, fmt_fecha(u.creado_en),
                    ), tags=() if u.activo else ("inactivo",))
        except Exception as exc:
            self.show_error(str(exc))

        self.user_tree.tag_configure("inactivo", foreground="#6b7280")

    def _sel_user_id(self):
        sel = self.user_tree.selection()
        if not sel:
            self.show_error("Selecciona un usuario.")
            return None
        return int(sel[0])

    def _nuevo_usuario(self):
        m = UsuarioFormModal(self, None, self.current_user)
        self.wait_window(m)
        self._load_users()

    def _editar_usuario(self):
        uid = self._sel_user_id()
        if uid:
            m = UsuarioFormModal(self, uid, self.current_user)
            self.wait_window(m)
            self._load_users()

    def _toggle_usuario(self):
        uid = self._sel_user_id()
        if not uid:
            return
        if uid == self.current_user.id:
            self.show_error("No puedes desactivar tu propia cuenta.")
            return
        from database import Usuario
        try:
            with self.get_session() as s:
                u = s.query(Usuario).get(uid)
                if u:
                    u.activo = not u.activo
                    s.commit()
            self._load_users()
        except Exception as exc:
            self.show_error(str(exc))

    # ─────────────────────────────────────────────────────
    #  TAB CATEGORÍAS
    # ─────────────────────────────────────────────────────

    def _build_cats(self, parent):
        top = ctk.CTkFrame(parent, fg_color="transparent", height=52)
        top.pack(fill="x", pady=(4, 6))
        top.pack_propagate(False)

        self._nueva_cat_var = tk.StringVar()
        ctk.CTkEntry(top, textvariable=self._nueva_cat_var,
                     placeholder_text="Nombre de nueva categoría",
                     width=240, height=32).pack(side="left", padx=4, pady=10)
        ctk.CTkButton(top, text="+ Añadir", command=self._nueva_cat,
                      fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
                      width=90, height=32).pack(side="left", padx=4)

        cols = [
            ("nombre",      "Nombre",      180),
            ("descripcion", "Descripción", 300),
            ("productos",   "Productos",    90, "e"),
        ]
        tframe, self.cat_tree = self.make_sortable_table(parent, cols)
        tframe.pack(fill="both", expand=True, pady=(0, 6))

        bar = ctk.CTkFrame(parent, fg_color="transparent", height=44)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        ctk.CTkButton(bar, text="Eliminar categoría", command=self._eliminar_cat,
                      fg_color="#7f1d1d", hover_color="#991b1b",
                      width=150, height=32).pack(side="left", padx=4)
        ctk.CTkLabel(bar, text="Solo se puede eliminar si no tiene productos asignados",
                     font=ctk.CTkFont(size=11), text_color="#6b7280").pack(side="left", padx=8)

    def _load_cats(self):
        from database import Categoria

        for row in self.cat_tree.get_children():
            self.cat_tree.delete(row)

        try:
            with self.get_session() as s:
                cats = s.query(Categoria).order_by(Categoria.nombre).all()
                for c in cats:
                    n_prod = len(c.productos)
                    self.cat_tree.insert("", "end", iid=str(c.id), values=(
                        c.nombre, c.descripcion or "—", n_prod,
                    ))
        except Exception as exc:
            self.show_error(str(exc))

    def _nueva_cat(self):
        nombre = self._nueva_cat_var.get().strip()
        if not nombre:
            self.show_error("Escribe el nombre de la categoría.")
            return
        from database import Categoria
        try:
            with self.get_session() as s:
                if s.query(Categoria).filter_by(nombre=nombre).first():
                    self.show_error(f"Ya existe la categoría '{nombre}'.")
                    return
                s.add(Categoria(nombre=nombre))
                s.commit()
            self._nueva_cat_var.set("")
            self._load_cats()
        except Exception as exc:
            self.show_error(str(exc))

    def _eliminar_cat(self):
        sel = self.cat_tree.selection()
        if not sel:
            self.show_error("Selecciona una categoría.")
            return
        cid = int(sel[0])
        from database import Categoria
        try:
            with self.get_session() as s:
                c = s.query(Categoria).get(cid)
                if not c:
                    return
                if c.productos:
                    self.show_error(f"No se puede eliminar '{c.nombre}': tiene {len(c.productos)} productos.")
                    return
                if not self.confirm(f"¿Eliminar la categoría '{c.nombre}'?"):
                    return
                s.delete(c)
                s.commit()
            self._load_cats()
        except Exception as exc:
            self.show_error(str(exc))

    # ─────────────────────────────────────────────────────
    #  TAB UBICACIONES
    # ─────────────────────────────────────────────────────

    def _build_ubics(self, parent):
        top = ctk.CTkFrame(parent, fg_color="transparent", height=52)
        top.pack(fill="x", pady=(4, 6))
        top.pack_propagate(False)

        self._nueva_ubic_var = tk.StringVar()
        ctk.CTkEntry(top, textvariable=self._nueva_ubic_var,
                     placeholder_text="Nombre de nueva ubicación",
                     width=240, height=32).pack(side="left", padx=4, pady=10)
        ctk.CTkButton(top, text="+ Añadir", command=self._nueva_ubic,
                      fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
                      width=90, height=32).pack(side="left", padx=4)

        cols = [
            ("nombre",    "Nombre",    250),
            ("productos", "Productos",  90, "e"),
        ]
        tframe, self.ubic_tree = self.make_sortable_table(parent, cols)
        tframe.pack(fill="both", expand=True, pady=(0, 6))

        bar = ctk.CTkFrame(parent, fg_color="transparent", height=44)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        ctk.CTkButton(bar, text="Eliminar ubicación", command=self._eliminar_ubic,
                      fg_color="#7f1d1d", hover_color="#991b1b",
                      width=150, height=32).pack(side="left", padx=4)
        ctk.CTkLabel(bar, text="Solo se puede eliminar si no tiene productos asignados",
                     font=ctk.CTkFont(size=11), text_color="#6b7280").pack(side="left", padx=8)

    def _load_ubics(self):
        from database import Ubicacion

        for row in self.ubic_tree.get_children():
            self.ubic_tree.delete(row)

        try:
            with self.get_session() as s:
                ubics = s.query(Ubicacion).order_by(Ubicacion.nombre).all()
                for u in ubics:
                    n_prod = len(u.productos)
                    self.ubic_tree.insert("", "end", iid=str(u.id), values=(
                        u.nombre, n_prod,
                    ))
        except Exception as exc:
            self.show_error(str(exc))

    def _nueva_ubic(self):
        nombre = self._nueva_ubic_var.get().strip()
        if not nombre:
            self.show_error("Escribe el nombre de la ubicación.")
            return
        from database import Ubicacion
        try:
            with self.get_session() as s:
                if s.query(Ubicacion).filter_by(nombre=nombre).first():
                    self.show_error(f"Ya existe la ubicación '{nombre}'.")
                    return
                s.add(Ubicacion(nombre=nombre))
                s.commit()
            self._nueva_ubic_var.set("")
            self._load_ubics()
        except Exception as exc:
            self.show_error(str(exc))

    def _eliminar_ubic(self):
        sel = self.ubic_tree.selection()
        if not sel:
            self.show_error("Selecciona una ubicación.")
            return
        uid = int(sel[0])
        from database import Ubicacion
        try:
            with self.get_session() as s:
                u = s.query(Ubicacion).get(uid)
                if not u:
                    return
                if u.productos:
                    self.show_error(f"No se puede eliminar '{u.nombre}': tiene {len(u.productos)} productos.")
                    return
                if not self.confirm(f"¿Eliminar la ubicación '{u.nombre}'?"):
                    return
                s.delete(u)
                s.commit()
            self._load_ubics()
        except Exception as exc:
            self.show_error(str(exc))

    # ─────────────────────────────────────────────────────
    #  TAB UNIDADES
    # ─────────────────────────────────────────────────────

    def _build_units(self, parent):
        top = ctk.CTkFrame(parent, fg_color="transparent", height=52)
        top.pack(fill="x", pady=(4, 6))
        top.pack_propagate(False)

        self._nueva_unit_var = tk.StringVar()
        ctk.CTkEntry(top, textvariable=self._nueva_unit_var,
                     placeholder_text="Nombre de nueva unidad",
                     width=240, height=32).pack(side="left", padx=4, pady=10)
        ctk.CTkButton(top, text="+ Añadir", command=self._nueva_unit,
                      fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
                      width=90, height=32).pack(side="left", padx=4)

        cols = [
            ("nombre",    "Nombre",    250),
            ("productos", "Productos",  90, "e"),
        ]
        tframe, self.unit_tree = self.make_sortable_table(parent, cols)
        tframe.pack(fill="both", expand=True, pady=(0, 6))

        bar = ctk.CTkFrame(parent, fg_color="transparent", height=44)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        ctk.CTkButton(bar, text="Eliminar unidad", command=self._eliminar_unit,
                      fg_color="#7f1d1d", hover_color="#991b1b",
                      width=140, height=32).pack(side="left", padx=4)
        ctk.CTkLabel(bar, text="Solo se puede eliminar si no tiene productos asignados",
                     font=ctk.CTkFont(size=11), text_color="#6b7280").pack(side="left", padx=8)

    def _load_units(self):
        from database import Unidad

        for row in self.unit_tree.get_children():
            self.unit_tree.delete(row)

        try:
            with self.get_session() as s:
                units = s.query(Unidad).order_by(Unidad.nombre).all()
                for u in units:
                    n_prod = len(u.productos)
                    self.unit_tree.insert("", "end", iid=str(u.id), values=(
                        u.nombre, n_prod,
                    ))
        except Exception as exc:
            self.show_error(str(exc))

    def _nueva_unit(self):
        nombre = self._nueva_unit_var.get().strip()
        if not nombre:
            self.show_error("Escribe el nombre de la unidad.")
            return
        from database import Unidad
        try:
            with self.get_session() as s:
                if s.query(Unidad).filter_by(nombre=nombre).first():
                    self.show_error(f"Ya existe la unidad '{nombre}'.")
                    return
                s.add(Unidad(nombre=nombre))
                s.commit()
            self._nueva_unit_var.set("")
            self._load_units()
        except Exception as exc:
            self.show_error(str(exc))

    def _eliminar_unit(self):
        sel = self.unit_tree.selection()
        if not sel:
            self.show_error("Selecciona una unidad.")
            return
        uid = int(sel[0])
        from database import Unidad
        try:
            with self.get_session() as s:
                u = s.query(Unidad).get(uid)
                if not u:
                    return
                if u.productos:
                    self.show_error(f"No se puede eliminar '{u.nombre}': tiene {len(u.productos)} productos.")
                    return
                if not self.confirm(f"¿Eliminar la unidad '{u.nombre}'?"):
                    return
                s.delete(u)
                s.commit()
            self._load_units()
        except Exception as exc:
            self.show_error(str(exc))

    # ─────────────────────────────────────────────────────
    #  REFRESH GLOBAL
    # ─────────────────────────────────────────────────────

    def refresh(self):
        self._load_users()
        self._load_cats()
        self._load_ubics()
        self._load_units()


# ─────────────────────────────────────────────────────────
#  MODAL USUARIO
# ─────────────────────────────────────────────────────────

class UsuarioFormModal(ModalBase):
    def __init__(self, parent, user_id, current_user):
        titulo = "Nuevo Usuario" if user_id is None else "Editar Usuario"
        super().__init__(parent, titulo, ancho=460, alto=420)
        self._uid  = user_id
        self._me   = current_user
        self._build_form()
        if user_id:
            self._load()
        self.add_buttons(self._guardar)

    def _get_session(self):
        from database import get_session
        return get_session()

    def _build_form(self):
        r = 0
        self.add_label("Nombre *", r); r += 1
        self.e_nombre = self.add_entry(r, "Nombre completo"); r += 1
        self.add_label("Email *", r); r += 1
        self.e_email = self.add_entry(r, "usuario@laboratorio.com"); r += 1
        self.add_label("Contraseña" + (" (dejar vacío para no cambiar)" if self._uid else " *"), r); r += 1
        self.e_pass = self.add_entry(r, "••••••••"); r += 1
        self.add_label("Rol", r); r += 1
        self.e_rol = self.add_combo(r, ["usuario", "admin"]); r += 1
        self.add_label("Estado", r); r += 1
        self.e_activo = self.add_combo(r, ["activo", "inactivo"]); r += 1

    def _load(self):
        from database import Usuario
        with self._get_session() as s:
            u = s.query(Usuario).get(self._uid)
            if not u:
                return
            self.e_nombre.insert(0, u.nombre)
            self.e_email.insert(0, u.email)
            self.e_rol.set(u.rol)
            self.e_activo.set("activo" if u.activo else "inactivo")

    def _guardar(self):
        from database import Usuario
        from tkinter import messagebox

        nombre = self.e_nombre.get().strip()
        email  = self.e_email.get().strip().lower()
        passwd = self.e_pass.get()
        rol    = self.e_rol.get()
        activo = self.e_activo.get() == "activo"

        if not nombre or not email:
            messagebox.showerror("Error", "Nombre y email son obligatorios.", parent=self)
            return
        if self._uid is None and not passwd:
            messagebox.showerror("Error", "La contraseña es obligatoria para nuevos usuarios.", parent=self)
            return

        with self._get_session() as s:
            if self._uid is None:
                if s.query(Usuario).filter_by(email=email).first():
                    messagebox.showerror("Error", f"Ya existe un usuario con email '{email}'.", parent=self)
                    return
                u = Usuario(activo=activo)
                s.add(u)
            else:
                u = s.query(Usuario).get(self._uid)
                existing = s.query(Usuario).filter(
                    Usuario.email == email, Usuario.id != self._uid).first()
                if existing:
                    messagebox.showerror("Error", f"Ese email ya está en uso.", parent=self)
                    return

            u.nombre = nombre
            u.email  = email
            u.rol    = rol
            u.activo = activo
            if passwd:
                u.set_password(passwd)

            s.commit()

        self.destroy()
