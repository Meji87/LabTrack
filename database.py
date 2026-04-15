"""
database.py — Modelos SQLAlchemy para LabTrack Desktop
Sin dependencias de Flask; compatible con SQLite en red (WAL mode).
"""

import os
import sys
from datetime import datetime, date
from sqlalchemy import (
    create_engine, event, text,
    Column, Integer, String, Float, Boolean, DateTime, Date, Text, ForeignKey,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

# Asegurar que config.py sea encontrado sea cual sea el directorio de trabajo
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from config import DATABASE_PATH, DOCUMENTOS_PATH, DIAS_CADUCIDAD_ALERTA


# ─────────────────────────────────────────────────────────
#  BASE
# ─────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ─────────────────────────────────────────────────────────
#  USUARIOS
# ─────────────────────────────────────────────────────────

class Usuario(Base):
    __tablename__ = "usuarios"

    id           = Column(Integer, primary_key=True)
    nombre       = Column(String(100), nullable=False)
    email        = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    rol          = Column(String(20), default="usuario")   # 'admin' | 'usuario'
    activo       = Column(Boolean, default=True)
    creado_en    = Column(DateTime, default=datetime.utcnow)

    movimientos = relationship("MovimientoStock", back_populates="usuario")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def es_admin(self) -> bool:
        return self.rol == "admin"

    def __repr__(self):
        return f"<Usuario {self.email}>"


# ─────────────────────────────────────────────────────────
#  PROVEEDORES
# ─────────────────────────────────────────────────────────

class Proveedor(Base):
    __tablename__ = "proveedores"

    id        = Column(Integer, primary_key=True)
    nombre    = Column(String(200), nullable=False)
    email     = Column(String(120))
    telefono  = Column(String(30))
    direccion = Column(Text)
    activo    = Column(Boolean, default=True)
    creado_en = Column(DateTime, default=datetime.utcnow)

    productos = relationship("Producto", back_populates="proveedor")
    pedidos   = relationship("Pedido",   back_populates="proveedor")

    def __repr__(self):
        return f"<Proveedor {self.nombre}>"


# ─────────────────────────────────────────────────────────
#  CATEGORÍAS
# ─────────────────────────────────────────────────────────

class Categoria(Base):
    __tablename__ = "categorias"

    id          = Column(Integer, primary_key=True)
    nombre      = Column(String(100), unique=True, nullable=False)
    descripcion = Column(Text)

    productos = relationship("Producto", back_populates="categoria")

    def __repr__(self):
        return f"<Categoria {self.nombre}>"


# ─────────────────────────────────────────────────────────
#  UBICACIONES
# ─────────────────────────────────────────────────────────

class Ubicacion(Base):
    __tablename__ = "ubicaciones"

    id     = Column(Integer, primary_key=True)
    nombre = Column(String(100), unique=True, nullable=False)

    productos = relationship("Producto", back_populates="ubicacion_rel")

    def __repr__(self):
        return f"<Ubicacion {self.nombre}>"


# ─────────────────────────────────────────────────────────
#  UNIDADES
# ─────────────────────────────────────────────────────────

class Unidad(Base):
    __tablename__ = "unidades"

    id     = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True, nullable=False)

    productos = relationship("Producto", back_populates="unidad_rel")

    def __repr__(self):
        return f"<Unidad {self.nombre}>"


# ─────────────────────────────────────────────────────────
#  PRODUCTOS
# ─────────────────────────────────────────────────────────

UNIDADES = ["ml", "L", "g", "kg", "mg", "unidades", "cajas", "ampollas", "viales", "otro"]
ESTADOS_PRODUCTO = ["activo", "consumido", "baja"]


class Producto(Base):
    __tablename__ = "productos"

    id              = Column(Integer, primary_key=True)
    nombre          = Column(String(200), nullable=False)
    referencia      = Column(String(100), unique=True, nullable=False)
    categoria_id    = Column(Integer, ForeignKey("categorias.id"))
    proveedor_id    = Column(Integer, ForeignKey("proveedores.id"))
    cantidad_actual = Column(Float, default=0)
    cantidad_minima = Column(Float, default=0)
    unidad          = Column(String(20), default="unidades")

    #numero_lote     = Column(String(100))
    #fecha_caducidad = Column(Date)
    tiene_lote       = Column(Boolean, default=False)  # ¿este producto usa lotes?
    tiene_caducidad  = Column(Boolean, default=False)  # ¿este producto caduca?
    lotes = relationship("LoteProducto", back_populates="producto", cascade="all, delete-orphan")

    estado          = Column(String(20), default="activo")
    descripcion     = Column(Text)
    ubicacion       = Column(String(100))
    unidad_id       = Column(Integer, ForeignKey("unidades.id"), nullable=True)
    ubicacion_id    = Column(Integer, ForeignKey("ubicaciones.id"), nullable=True)
    creado_en       = Column(DateTime, default=datetime.utcnow)
    actualizado_en  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    categoria     = relationship("Categoria",  back_populates="productos")
    proveedor     = relationship("Proveedor",  back_populates="productos")
    movimientos   = relationship("MovimientoStock", back_populates="producto")
    lineas_pedido = relationship("LineaPedido", back_populates="producto")
    ubicacion_rel = relationship("Ubicacion",  back_populates="productos")
    unidad_rel    = relationship("Unidad",     back_populates="productos")

    @property
    def nombre_unidad(self) -> str:
        if self.unidad_rel:
            return self.unidad_rel.nombre
        return self.unidad or ""

    @property
    def nombre_ubicacion(self) -> str:
        if self.ubicacion_rel:
            return self.ubicacion_rel.nombre
        return self.ubicacion or ""

    @property
    def stock_bajo(self) -> bool:
        return self.cantidad_actual <= self.cantidad_minima and self.cantidad_minima > 0

    # @property
    # def dias_para_caducar(self):
    #     if self.fecha_caducidad:
    #         return (self.fecha_caducidad - date.today()).days
    #     return None

    # @property
    # def por_caducar(self) -> bool:
    #     d = self.dias_para_caducar
    #     return d is not None and 0 <= d <= DIAS_CADUCIDAD_ALERTA

    # @property
    # def caducado(self) -> bool:
    #     d = self.dias_para_caducar
    #     return d is not None and d < 0

    def __repr__(self):
        return f"<Producto {self.referencia} - {self.nombre}>"


# ─────────────────────────────────────────────────────────
#  LOTES
# ─────────────────────────────────────────────────────────
class LoteProducto(Base):
    __tablename__ = "lotes_producto"

    id              = Column(Integer, primary_key=True)
    producto_id     = Column(Integer, ForeignKey("productos.id"), nullable=False)
    recepcion_id    = Column(Integer, ForeignKey("recepciones.id"), nullable=True)
    numero_lote     = Column(String(100))
    fecha_caducidad = Column(Date, nullable=True)
    cantidad        = Column(Float, default=0)
    creado_en       = Column(DateTime, default=datetime.utcnow)

    producto  = relationship("Producto", back_populates="lotes")
    recepcion = relationship("Recepcion", back_populates="lotes")


# ─────────────────────────────────────────────────────────
#  PEDIDOS
# ─────────────────────────────────────────────────────────

ESTADOS_PEDIDO = ["borrador", "pendiente", "enviado", "recibido", "cancelado"]


class Pedido(Base):
    __tablename__ = "pedidos"

    id             = Column(Integer, primary_key=True)
    numero         = Column(String(50), unique=True, nullable=False)
    proveedor_id   = Column(Integer, ForeignKey("proveedores.id"), nullable=False)
    estado         = Column(String(20), default="borrador")
    notas          = Column(Text)
    fecha_pedido   = Column(DateTime, default=datetime.utcnow)
    fecha_envio    = Column(DateTime)
    creado_por_id  = Column(Integer, ForeignKey("usuarios.id"))

    proveedor  = relationship("Proveedor", back_populates="pedidos")
    lineas     = relationship("LineaPedido", back_populates="pedido", cascade="all, delete-orphan")
    recepcion  = relationship("Recepcion", back_populates="pedido", uselist=False)
    creado_por = relationship("Usuario")

    def __repr__(self):
        return f"<Pedido {self.numero}>"


class LineaPedido(Base):
    __tablename__ = "lineas_pedido"

    id               = Column(Integer, primary_key=True)
    pedido_id        = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    producto_id      = Column(Integer, ForeignKey("productos.id"), nullable=False)
    cantidad_pedida  = Column(Float, nullable=False)
    precio_unitario  = Column(Float)
    notas            = Column(String(200))

    pedido   = relationship("Pedido",   back_populates="lineas")
    producto = relationship("Producto", back_populates="lineas_pedido")


# ─────────────────────────────────────────────────────────
#  RECEPCIONES
# ─────────────────────────────────────────────────────────

class Recepcion(Base):
    __tablename__ = "recepciones"

    id               = Column(Integer, primary_key=True)
    pedido_id        = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    fecha_recepcion  = Column(DateTime, default=datetime.utcnow)
    numero_albaran   = Column(String(100))
    numero_factura   = Column(String(100))
    archivo_albaran  = Column(String(300))
    archivo_factura  = Column(String(300))
    notas            = Column(Text)
    recibido_por_id  = Column(Integer, ForeignKey("usuarios.id"))

    pedido       = relationship("Pedido",   back_populates="recepcion")
    recibido_por = relationship("Usuario")

    lotes = relationship("LoteProducto", back_populates="recepcion")

    def __repr__(self):
        return f"<Recepcion pedido={self.pedido_id}>"


# ─────────────────────────────────────────────────────────
#  MOVIMIENTOS DE STOCK
# ─────────────────────────────────────────────────────────

TIPOS_MOVIMIENTO = ["entrada", "consumo", "baja", "ajuste", "recepcion"]


class MovimientoStock(Base):
    __tablename__ = "movimientos_stock"

    id                = Column(Integer, primary_key=True)
    producto_id       = Column(Integer, ForeignKey("productos.id"), nullable=False)
    usuario_id        = Column(Integer, ForeignKey("usuarios.id"))
    tipo              = Column(String(20), nullable=False)
    cantidad          = Column(Float, nullable=False)
    cantidad_anterior = Column(Float)
    cantidad_posterior = Column(Float)
    motivo            = Column(String(300))
    referencia_doc    = Column(String(100))
    fecha             = Column(DateTime, default=datetime.utcnow)

    producto = relationship("Producto", back_populates="movimientos")
    usuario  = relationship("Usuario",  back_populates="movimientos")

    def __repr__(self):
        return f"<Movimiento {self.tipo} {self.cantidad}>"


# ─────────────────────────────────────────────────────────
#  ENGINE Y SESSION FACTORY
# ─────────────────────────────────────────────────────────

def _build_engine():
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    eng = create_engine(
        f"sqlite:///{DATABASE_PATH}",
        connect_args={"check_same_thread": False, "timeout": 30},
        pool_pre_ping=True,
    )

    @event.listens_for(eng, "connect")
    def _set_pragmas(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")   # acceso concurrente en red
        cur.execute("PRAGMA busy_timeout=5000")   # esperar hasta 5 s si BD bloqueada
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    return eng


engine       = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session():
    """Devuelve una sesión SQLAlchemy. Úsala como context manager: `with get_session() as s:`"""
    return SessionLocal()


def init_db():
    """Crea tablas y datos iniciales si no existen."""
    Base.metadata.create_all(engine)
    os.makedirs(DOCUMENTOS_PATH, exist_ok=True)

    # Migraciones: añadir columnas FK a tabla productos si no existen
    with engine.connect() as conn:
        for sql in [
            "ALTER TABLE productos ADD COLUMN unidad_id INTEGER REFERENCES unidades(id)",
            "ALTER TABLE productos ADD COLUMN ubicacion_id INTEGER REFERENCES ubicaciones(id)",
        ]:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                pass  # columna ya existe

    with SessionLocal() as s:
        # Admin por defecto
        if not s.query(Usuario).filter_by(email="admin@labtrack.com").first():
            admin = Usuario(nombre="Administrador", email="admin@labtrack.com", rol="admin")
            admin.set_password("admin123")
            s.add(admin)

        # Categorías por defecto
        for nombre in ["Reactivos", "Medios de cultivo", "Material fungible",
                        "Equipamiento", "Soluciones", "Antibióticos", "Enzimas", "Otro"]:
            if not s.query(Categoria).filter_by(nombre=nombre).first():
                s.add(Categoria(nombre=nombre))

        # Unidades por defecto
        for nombre in UNIDADES:
            if not s.query(Unidad).filter_by(nombre=nombre).first():
                s.add(Unidad(nombre=nombre))

        s.commit()
