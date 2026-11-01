# Arquitectura

## Stack

| Pieza | Versión / detalle |
| --- | --- |
| Python | 3.12.3 (venv en `venv/`) |
| Django | 6.1.2 (`asgiref 3.13.0`, `sqlparse 0.6.0`; no hay más dependencias) |
| Base de datos | SQLite, `db.sqlite3` en la raíz |
| CSS | Tailwind CSS vía CDN (`cdn.tailwindcss.com`) + `core/static/css/app.css` |
| Fuente | DM Sans desde Google Fonts |
| JS | Vanilla, un único archivo `core/static/js/script.js` |

## Estructura

```text
erp_project/
├── erp_project/        # Proyecto Django: settings.py, urls.py, wsgi/asgi
├── core/               # Dashboard, layout base, catálogo de módulos (modules.py), context processor, estáticos
├── users/              # Modelo User propio, Role, UserRole, login/logout, admin, permissions.py
├── materials/          # CRUD de materiales + filtros + paginación + export CSV
├── suppliers/          # Módulo de proveedores (en construcción)
├── db.sqlite3          # BD de desarrollo local (ignorada por .gitignore)
├── venv/               # Entorno virtual (ignorado por .gitignore)
├── requirements.txt    # Dependencias fijadas
├── erp_project.code-workspace
└── manage.py
```

`erp_project.code-workspace` (raíz) es el workspace de VS Code del proyecto.

## Configuración relevante (`erp_project/settings.py`)

- `AUTH_USER_MODEL = 'users.User'`.
- `LANGUAGE_CODE = 'es'`, `TIME_ZONE = 'UTC'`, `USE_TZ = True`.
- Context processor propio: `core.context_processors.get_permissions` (inyecta
  `permissions`, `roles` y `user_modules` en todas las plantillas).
- `LOGIN_URL = 'login'`, `LOGIN_REDIRECT_URL = 'dashboard'`,
  `LOGOUT_REDIRECT_URL = 'login'` (nombres de URL, no rutas).
- `DEBUG = True`, `ALLOWED_HOSTS = []`, `SECRET_KEY` en el código: solo desarrollo.
- `MAILERS` con backend de consola.
- No hay `STATIC_ROOT` ni `TEMPLATES['DIRS']`; todo se resuelve con `APP_DIRS`.

## Rutas

`erp_project/urls.py` monta `users.urls` y `core.urls` en la raíz y `materials.urls`
en `/materials/`. `suppliers` todavía no tiene `urls.py`.

| URL | Nombre | Vista | Protección |
| --- | --- | --- | --- |
| `/admin/` | — | Django admin | staff |
| `/login/` | `login` | `users.views.login_view` | pública |
| `/logout/` | `logout` | `users.views.logout_view` (solo POST, con CSRF) | `login_required` |
| `/dashboard/` | `dashboard` | `core.views.dashboard_view` | `login_required` |
| `/materials/` | `materials:materials_list` | lista, filtros, CSV | login + permiso ≥ 1 |
| `/materials/create/` | `materials:material_create` | alta | login + permiso 2 |
| `/materials/<pk>/edit/` | `materials:material_edit` | edición | login + permiso 2 |
| `/materials/<pk>/delete/` | `materials:material_delete` | borrado (POST) | login + permiso 2 |

Solo `materials` usa `app_name` (namespace). `users` y `core` no tienen namespace, por
eso se referencian como `'login'`, `'logout'`, `'dashboard'`.

## Flujo de una petición autenticada

1. `login_view` valida `LoginForm` (subclase de `AuthenticationForm`) y redirige a
   `dashboard`.
2. Cada render pasa por `get_permissions`, que usa `users/permissions.py` para calcular
   el nivel máximo por módulo y los nombres de rol.
3. `base.html` usa `permissions` para mostrar u ocultar enlaces del menú; las vistas de
   `materials` validan su nivel con `get_module_permission(request.user, 'materials')`.

Detalle de permisos en [permisos.md](permisos.md).
