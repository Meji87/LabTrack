"""
helpers.py — Funciones auxiliares de LabTrack Desktop
"""

import os
import shutil
from datetime import datetime, date
import sys

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from config import DOCUMENTOS_PATH


# ─────────────────────────────────────────────────────────
#  NUMERACIÓN DE PEDIDOS
# ─────────────────────────────────────────────────────────

def generar_numero_pedido(session) -> str:
    """Genera PED-YYYYMMDD-NNN único para hoy."""
    from database import Pedido
    hoy     = datetime.now()
    prefijo = f"PED-{hoy.strftime('%Y%m%d')}-"
    ultimo  = (session.query(Pedido)
               .filter(Pedido.numero.like(f"{prefijo}%"))
               .order_by(Pedido.numero.desc())
               .first())
    n = 1
    if ultimo:
        try:
            n = int(ultimo.numero.rsplit("-", 1)[-1]) + 1
        except ValueError:
            n = 1
    return f"{prefijo}{n:03d}"


# ─────────────────────────────────────────────────────────
#  GESTIÓN DE DOCUMENTOS PDF
# ─────────────────────────────────────────────────────────

def guardar_documento(ruta_origen: str, tipo: str, numero_doc: str) -> str | None:
    """
    Copia un PDF al directorio de documentos organizado por año/mes.

    Returns:
        Ruta relativa dentro de DOCUMENTOS_PATH, o None si falla.
    """
    if not ruta_origen or not os.path.isfile(ruta_origen):
        return None
    if not ruta_origen.lower().endswith(".pdf"):
        return None

    ahora   = datetime.now()
    subdir  = os.path.join(str(ahora.year), f"{ahora.month:02d}")
    dest_dir = os.path.join(DOCUMENTOS_PATH, subdir)
    os.makedirs(dest_dir, exist_ok=True)

    num_safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(numero_doc))
    ts       = ahora.strftime("%H%M%S")
    nombre   = f"{tipo}_{num_safe}_{ts}.pdf"
    dest     = os.path.join(dest_dir, nombre)
    shutil.copy2(ruta_origen, dest)

    return os.path.join(subdir, nombre)


def get_ruta_documento(ruta_relativa: str) -> str | None:
    """Devuelve la ruta absoluta de un documento guardado, o None si no existe."""
    if not ruta_relativa:
        return None
    ruta = os.path.join(DOCUMENTOS_PATH, ruta_relativa)
    return ruta if os.path.isfile(ruta) else None


def abrir_pdf(ruta_relativa: str):
    """Abre un PDF con el visor por defecto del sistema."""
    import subprocess
    ruta = get_ruta_documento(ruta_relativa)
    if ruta:
        if sys.platform == "win32":
            os.startfile(ruta)
        elif sys.platform == "darwin":
            subprocess.call(["open", ruta])
        else:
            subprocess.call(["xdg-open", ruta])
        return True
    return False


# ─────────────────────────────────────────────────────────
#  ALERTAS
# ─────────────────────────────────────────────────────────

def get_alertas(session) -> dict:
    from database import Producto, LoteProducto
    from sqlalchemy.orm import joinedload
    from config import DIAS_CADUCIDAD_ALERTA

    hoy = date.today()

    activos = (session.query(Producto)
               .options(joinedload(Producto.proveedor))
               .filter(Producto.estado == "activo").all())
    stock_bajo = [p for p in activos if p.stock_bajo]

    lotes_activos = (
        session.query(LoteProducto)
        .join(Producto)
        .options(joinedload(LoteProducto.producto).joinedload(Producto.proveedor))
        .filter(Producto.estado == "activo")
        .filter(LoteProducto.fecha_caducidad != None)
        .filter(LoteProducto.cantidad > 0)
        .all()
    )

    por_caducar = [l for l in lotes_activos
                   if 0 <= (l.fecha_caducidad - hoy).days <= DIAS_CADUCIDAD_ALERTA]
    caducados   = [l for l in lotes_activos
                   if (l.fecha_caducidad - hoy).days < 0]

    return {
        "stock_bajo":  stock_bajo,
        "por_caducar": por_caducar,
        "caducados":   caducados,
        "total":       len(stock_bajo) + len(por_caducar) + len(caducados),
    }


# ─────────────────────────────────────────────────────────
#  FORMATO
# ─────────────────────────────────────────────────────────

def fmt_fecha(d) -> str:
    if d is None:
        return "—"
    if isinstance(d, datetime):
        return d.strftime("%d/%m/%Y %H:%M")
    if isinstance(d, date):
        return d.strftime("%d/%m/%Y")
    return str(d)


def fmt_fecha_corta(d) -> str:
    if d is None:
        return "—"
    if isinstance(d, (datetime, date)):
        return d.strftime("%d/%m/%Y")
    return str(d)


def parse_fecha(s: str):
    """Convierte 'DD/MM/YYYY' (o variantes) a objeto date, o None."""
    s = s.strip()
    if not s or s in ("—", "-", ""):
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def fmt_qty(cantidad, unidad: str = "") -> str:
    if cantidad is None:
        return "—"
    txt = str(int(cantidad)) if cantidad == int(cantidad) else f"{cantidad:.2f}"
    return f"{txt} {unidad}".strip()
