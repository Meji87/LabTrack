# LabTrack Desktop — Contexto del proyecto

## Stack
- Python + CustomTkinter (GUI de escritorio, modo dark)
- SQLite via SQLAlchemy ORM (`labstock.db`)
- Werkzeug para hashing de contraseñas
- Estructura: `main.py`, `database.py`, `config.py`, `views/`, `utils/`

## Arquitectura principal (`main.py`)
- Clase principal: `LabTrackApp(ctk.CTk)`
- `self.current_user` → objeto `Usuario` (SQLAlchemy ORM) con `.nombre`, `.rol`, `.es_admin`
- Flujo actual: `__init__` → `_init_session()` → `_show_main()` (sin login)
- `_init_session()` busca/crea usuario en BD por `getpass.getuser()` con email `{user}@labtrack.local`
- `_show_main()` construye sidebar + área de contenido
- `_navigate(key)` carga vistas desde `views/`
- Acceso a Admin protegido por contraseña via modal personalizado `_ask_admin_password()` con show="*"

## Modelos en database.py
- `Usuario`: id, nombre, email, password_hash, rol, activo
- `Producto`: tiene_lote, tiene_caducidad, ubicacion_id (FK a Ubicacion), unidad_id (FK a Unidad)
  - Propiedades: `nombre_unidad`, `nombre_ubicacion` (prefieren FK, caen en texto legacy)
- `LoteProducto`: producto_id, recepcion_id, numero_lote, fecha_caducidad, cantidad
- `Pedido` / `LineaPedido`: precio_unitario existe en modelo pero oculto en UI
- `Recepcion`: fecha_recepcion (editable al crear), pedido_id, lotes[]
- `MovimientoStock`: tipo ∈ ["entrada","consumo","baja","ajuste","recepcion"]
- `Categoria`, `Ubicacion`, `Unidad`: gestionadas desde Admin
- `base_view.py`: método `make_sortable_table` disponible (ordena por columna al clicar encabezado)

## Estado actual — todo implementado
- Sin pantalla de login, usuario se obtiene de Windows
- Admin protegido con contraseña (modal con show="*" e icono)
- Ubicacion y Unidad son modelos en BD, gestionables desde Admin
- Estado "consumido" automático al llegar cantidad a 0; "baja" solo manual
- Recepciones parciales: pedido queda "pendiente" si cantidad recibida < pedida
- Movimientos: entrada pide lote/caducidad si aplica; consumo selecciona lote
- Todas las tablas son ordenables clicando encabezado
- products_view tiene búsqueda por texto, filtro por categoría, filtro por estado, checkbox solo stock bajo

## Tareas pendientes

### products_view.py
- Botón "Ver lotes" en cada fila de producto (o en el detalle del producto al seleccionar).
  Solo visible si `producto.tiene_lote = True`.
  Abre modal con tabla: número de lote, cantidad, fecha caducidad, días restantes.
  Días restantes en rojo si < 0 (caducado), naranja si < 30.

### Exportar CSV
- `products_view.py`: botón "Exportar CSV" que descarga los productos visibles en la tabla (respetando filtros activos).
- `movements_view.py`: botón "Exportar CSV" que descarga los movimientos visibles.
- El archivo se guarda con diálogo filedialog.asksaveasfilename, nombre por defecto con fecha de hoy.

### Sidebar — Acerca de (main.py + config.py)
- Añadir a config.py si no existen:
  VERSION  = "1.0.0"
  AUTOR    = "Marc Mestres Mejias"
  CONTACTO = "mmestres@destileriasmg.com"
- Añadir botón "ℹ  Acerca de" en el sidebar, entre los botones de navegación y el botón "Salir".
- Al clicar abre un modal (ModalBase) con: icono de la app, imagen de la app, nombre app, versión, autor, contacto.
