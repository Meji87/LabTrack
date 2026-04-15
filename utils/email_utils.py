"""
email_utils.py — Envío de emails con smtplib (sin Flask-Mail)
"""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import sys

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from config import (MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS,
                    MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER)


def _send(to: str, subject: str, html: str) -> tuple[bool, str]:
    """Envía un email HTML. Devuelve (éxito, mensaje)."""
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        return False, ("Email no configurado.\n"
                       "Edita MAIL_USERNAME y MAIL_PASSWORD en config.py")
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = MAIL_DEFAULT_SENDER
        msg["To"]      = to
        msg.attach(MIMEText(html, "html", "utf-8"))

        ctx = ssl.create_default_context()
        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as server:
            if MAIL_USE_TLS:
                server.starttls(context=ctx)
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.sendmail(MAIL_USERNAME, to, msg.as_string())

        return True, "Email enviado correctamente."

    except smtplib.SMTPAuthenticationError:
        return False, "Error de autenticación SMTP. Verifica credenciales en config.py."
    except smtplib.SMTPException as exc:
        return False, f"Error SMTP: {exc}"
    except Exception as exc:
        return False, f"Error al enviar email: {exc}"


def enviar_pedido_proveedor(pedido) -> tuple[bool, str]:
    """Envía el pedido al proveedor por email."""
    if not pedido.proveedor.email:
        return False, f"El proveedor '{pedido.proveedor.nombre}' no tiene email."

    filas = ""
    for l in pedido.lineas:
        precio = f"{l.precio_unitario:.2f} €" if l.precio_unitario else "—"
        filas += f"""
        <tr>
          <td style="padding:8px;border-bottom:1px solid #ddd">{l.producto.nombre}</td>
          <td style="padding:8px;border-bottom:1px solid #ddd">{l.producto.referencia}</td>
          <td style="padding:8px;border-bottom:1px solid #ddd;text-align:center">
              {l.cantidad_pedida} {l.producto.unidad}</td>
          <td style="padding:8px;border-bottom:1px solid #ddd;text-align:right">{precio}</td>
          <td style="padding:8px;border-bottom:1px solid #ddd">{l.notas or ''}</td>
        </tr>"""

    html = f"""<html><body style="font-family:Arial,sans-serif;color:#333">
    <div style="max-width:700px;margin:0 auto;padding:20px">
      <h2 style="color:#0d5c3d;border-bottom:2px solid #10b981;padding-bottom:8px">
        Pedido {pedido.numero}</h2>
      <p><b>Fecha:</b> {pedido.fecha_pedido.strftime('%d/%m/%Y')}</p>
      <p><b>Proveedor:</b> {pedido.proveedor.nombre}</p>
      {f'<p><b>Notas:</b> {pedido.notas}</p>' if pedido.notas else ''}
      <h3 style="color:#0d5c3d">Productos solicitados</h3>
      <table style="width:100%;border-collapse:collapse;font-size:14px">
        <thead>
          <tr style="background:#0d5c3d;color:#fff">
            <th style="padding:10px;text-align:left">Producto</th>
            <th style="padding:10px;text-align:left">Referencia</th>
            <th style="padding:10px;text-align:center">Cantidad</th>
            <th style="padding:10px;text-align:right">Precio unit.</th>
            <th style="padding:10px;text-align:left">Notas</th>
          </tr>
        </thead>
        <tbody>{filas}</tbody>
      </table>
      <p style="margin-top:30px;font-size:11px;color:#888">
        Generado automáticamente por LabTrack.</p>
    </div></body></html>"""

    return _send(pedido.proveedor.email,
                 f"Pedido {pedido.numero} — Laboratorio", html)


def enviar_confirmacion_recepcion(recepcion) -> tuple[bool, str]:
    """Envía confirmación de recepción al proveedor."""
    pedido = recepcion.pedido
    if not pedido.proveedor.email:
        return False, f"El proveedor '{pedido.proveedor.nombre}' no tiene email."

    html = f"""<html><body style="font-family:Arial,sans-serif;color:#333">
    <div style="max-width:600px;margin:0 auto;padding:20px">
      <h2 style="color:#0d5c3d;border-bottom:2px solid #10b981;padding-bottom:8px">
        Confirmación de recepción</h2>
      <p>Se confirma la recepción del pedido <b>{pedido.numero}</b>.</p>
      <ul>
        <li><b>Fecha de recepción:</b> {recepcion.fecha_recepcion.strftime('%d/%m/%Y')}</li>
        {'<li><b>Nº Albarán:</b> ' + recepcion.numero_albaran + '</li>' if recepcion.numero_albaran else ''}
        {'<li><b>Nº Factura:</b> ' + recepcion.numero_factura + '</li>' if recepcion.numero_factura else ''}
        {'<li><b>Notas:</b> ' + recepcion.notas + '</li>' if recepcion.notas else ''}
      </ul>
      <p style="font-size:11px;color:#888">Generado automáticamente por LabTrack.</p>
    </div></body></html>"""

    return _send(pedido.proveedor.email,
                 f"Confirmación recepción pedido {pedido.numero}", html)
