# Estado y siguientes pasos

## Estado por módulo (2026-10-30)

| Módulo | Campo en `Role` | Estado |
| --- | --- | --- |
| Autenticación | — | Hecho (login/logout) |
| Usuarios y roles | — | Hecho, gestionado desde `/admin/` |
| Dashboard | — | Hecho; solo la tarjeta de Materiales enlaza a algo |
| Materiales | `materials` | CRUD, filtros, paginación y CSV |
| Proveedores | `suppliers` | Modelo y formulario sin commitear; falta migración, vistas, URLs, plantillas |
| Clientes | `customers` | No iniciado |
| Compras | `purchases` | No iniciado |
| Ventas | `sales` | No iniciado |
| Inventario | `inventory` | No iniciado |
| Contabilidad | `accounting` | No iniciado |
| Reportes | `reporting` | No iniciado |

## Historial de git

```text
9f74a40 :sparkles: Se agrego el modulo de materiales
6bfb02e :memo: Actulizando el readme
07e975f :tada: Mi primer commit
d6abe34 :tada: Mi first commit
```

Sin commitear: `suppliers/` completo y su alta en `INSTALLED_APPS`, `docs/`, las
correcciones del 2026-10-30 (incluye `users/permissions.py`, pruebas, README y el workspace movido a la raíz), `.gitignore`, `requirements.txt` y la baja de `venv/`, `*.pyc` y `db.sqlite3` del índice.

## Siguientes pasos sugeridos (en orden)

1. Commitear las correcciones del 2026-10-30 (incluye la baja de `venv/`, `*.pyc` y
   `db.sqlite3` del índice).
2. Ajustar el modelo de `suppliers` (`CharField` para teléfono y CP, nombre singular),
   generar la migración y completar vistas/URLs/plantillas siguiendo
   [convenciones.md](convenciones.md).
3. Mantener la batería de pruebas al añadir módulos (ver [convenciones.md](convenciones.md)).
4. Preparar la configuración de producción (ver [problemas-conocidos.md](problemas-conocidos.md)).
