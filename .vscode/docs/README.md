# Documentación de contexto — ERP Project

Contexto técnico del proyecto para retomar el trabajo (personas o agentes) sin tener
que releer todo el código. Revisión inicial: **2026-10-30**; actualizado al commit `d5dcd27`.

| Documento | Contenido |
| --- | --- |
| [arquitectura.md](arquitectura.md) | Stack, apps, configuración, rutas y flujo de peticiones |
| [modelos.md](modelos.md) | Modelos, tablas, migraciones y datos actuales en la BD |
| [permisos.md](permisos.md) | Sistema de roles y permisos por módulo, y dónde se aplica |
| [frontend.md](frontend.md) | Plantillas, estilos, JavaScript y convenciones de UI |
| [problemas-conocidos.md](problemas-conocidos.md) | Bugs confirmados, riesgos y deuda técnica, por prioridad |
| [convenciones.md](convenciones.md) | Patrón para crear un módulo nuevo y estilo de código del repo |
| [estado-y-roadmap.md](estado-y-roadmap.md) | Estado por módulo y siguientes pasos sugeridos |

## Resumen en 30 segundos

- ERP web en **Django 6.1.2 / Python 3.12 / SQLite**, UI con **Tailwind por CDN**.
- Apps: `users` (auth + roles), `core` (dashboard + layout), `materials` (CRUD completo),
  `suppliers` (en construcción: solo modelo y formulario, sin migración ni vistas).
- Permisos propios: cada `Role` tiene un entero 0/1/2 por módulo; un usuario puede tener
  varios roles y gana el nivel máximo.
- Dependencias en `requirements.txt`; `.gitignore` excluye `venv/`, `__pycache__/` y
  `db.sqlite3` (cada quien usa su BD local). 25 pruebas automatizadas.
- Pendientes y bugs abiertos: ver [problemas-conocidos.md](problemas-conocidos.md).

## Cómo arrancar

```bash
cd ~/erp_project
source venv/bin/activate          # el venv real se llama venv/, no .venv/
pip install -r requirements.txt
python manage.py runserver
# http://127.0.0.1:8000/login/
```

Comandos de verificación (resultado al 2026-10-30):

| Comando | Resultado |
| --- | --- |
| `python manage.py check` | Sin problemas |
| `python manage.py makemigrations --check` | Falta `suppliers/migrations/0001_initial.py` |
| `python manage.py test` | 25 pruebas, todas OK |
