# Estado y siguientes pasos

## Estado por módulo (2026-10-30)

| Módulo | Campo en `Role` | Estado |
| --- | --- | --- |
| Autenticación | — | Hecho (login/logout) |
| Usuarios y roles | — | Hecho, gestionado desde `/admin/` |
| Dashboard | — | Hecho; solo la tarjeta de Materiales enlaza a algo |
| Materiales | `materials` | CRUD, filtros, paginación y CSV |
| Proveedores | `suppliers` | Modelo y formulario; falta migración, vistas, URLs, plantillas |
| Clientes | `customers` | No iniciado |
| Compras | `purchases` | No iniciado |
| Ventas | `sales` | No iniciado |
| Inventario | `inventory` | No iniciado |
| Contabilidad | `accounting` | No iniciado |
| Reportes | `reporting` | No iniciado |

## Historial de git

```text
d5dcd27 :zap: Optimizacion del proyecto
dd31744 :wrench: Se realizaron ajustes en el proyecto
9f74a40 :sparkles: Se agrego el modulo de materiales
6bfb02e :memo: Actulizando el readme
07e975f :tada: Mi primer commit
d6abe34 :tada: Mi first commit
```

`dd31744` y `d5dcd27` incluyen las correcciones del 2026-10-30: permisos centralizados
en `users/permissions.py`, pruebas, `.gitignore`, `requirements.txt`, README y la baja
de `venv/`, `*.pyc` y `db.sqlite3` del repositorio.

La rama `rediseno-taller` contiene el rediseño visual del portal (tema "Taller", ver
[frontend.md](frontend.md)), el catálogo de módulos `core/modules.py` y las mejoras de
login, dashboard y materiales del 2026-10-30 / 31.

## Siguientes pasos sugeridos (en orden)

1. Ajustar el modelo de `suppliers` (`CharField` para teléfono y CP, nombre singular),
   generar la migración y completar vistas/URLs/plantillas siguiendo
   [convenciones.md](convenciones.md).
2. Mantener la batería de pruebas al añadir módulos (ver [convenciones.md](convenciones.md)).
3. Preparar la configuración de producción (ver [problemas-conocidos.md](problemas-conocidos.md)).
