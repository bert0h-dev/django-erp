# Problemas conocidos

Problemas abiertos del proyecto. Revisión del 2026-10-30. Cuando uno se corrige, se elimina de este documento.

## Alta prioridad

1. **`suppliers` sin migración.** La app está en `INSTALLED_APPS` pero `makemigrations --check` detecta cambios pendientes. Revisar el modelo antes de generarla (ver [modelos.md](modelos.md)).

## Antes de producción

`SECRET_KEY` en el código, `DEBUG = True`, `ALLOWED_HOSTS = []`, sin `STATIC_ROOT`, Tailwind por CDN, SQLite, `TIME_ZONE = 'UTC'` (posiblemente se quiera la zona local).
