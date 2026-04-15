# config.py — Configuración principal de LabTrack Desktop
#
# PARA USO EN RED:
#   Cambia BASE_DIR_DATOS para apuntar a la carpeta compartida de red.
#
#   Ejemplos:
#     Ruta UNC Windows : BASE_DIR_DATOS = r"\\servidor\compartido\labstock"
#     Unidad mapeada   : BASE_DIR_DATOS = r"Z:\labstock"
#     Local (defecto)  : BASE_DIR_DATOS = BASE_DIR

import os

# Directorio donde reside este archivo (junto a main.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
#  RUTA DE DATOS  ← cambia esto para apuntar a la red
# ============================================================
BASE_DIR_DATOS = BASE_DIR

# Rutas derivadas (no editar salvo que sepas lo que haces)
DATABASE_PATH  = os.path.join(BASE_DIR_DATOS, "labstock.db")
DOCUMENTOS_PATH = os.path.join(BASE_DIR_DATOS, "documentos")

# ============================================================
#  CONFIGURACIÓN DE EMAIL (Gmail con contraseña de app)
#  Guía contraseña de app: https://myaccount.google.com/apppasswords
# ============================================================
MAIL_SERVER  = "smtp.gmail.com"
MAIL_PORT    = 587
MAIL_USE_TLS = True
MAIL_USERNAME = ""          # Ej: "laboratorio@gmail.com"
MAIL_PASSWORD = ""          # Contraseña de aplicación de Gmail
MAIL_DEFAULT_SENDER = "LabTrack <labtrack@laboratorio.com>"

# ============================================================
#  ALERTAS
# ============================================================
DIAS_CADUCIDAD_ALERTA = 30  # Días antes de caducidad para alertar

# ============================================================
#  INTERFAZ
# ============================================================
APP_TITULO    = "LabTrack — Gestión de Laboratorio"
APP_ANCHO     = 1280
APP_ALTO      = 800
APP_MIN_ANCHO = 1100
APP_MIN_ALTO  = 650

# Paleta de colores
COLOR_SIDEBAR_BG    = "#1e2329"
COLOR_SIDEBAR_HOVER = "#2d333b"
COLOR_SIDEBAR_ACTIVE = "#0d5c3d"
COLOR_ACCENT        = "#10b981"   # verde esmeralda
COLOR_ACCENT_HOVER  = "#059669"
COLOR_DANGER        = "#ef4444"
COLOR_WARNING       = "#f59e0b"
COLOR_SUCCESS       = "#22c55e"
COLOR_INFO          = "#3b82f6"
COLOR_HEADER_BG     = "#161b22"
COLOR_CARD_BG       = "#21262d"
COLOR_TABLE_BG      = "#0d1117"
COLOR_TABLE_ROW_ALT = "#161b22"
