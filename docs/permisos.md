# Roles y permisos

El proyecto no usa los permisos/grupos nativos de Django para los módulos. Usa un
esquema propio en `users.models.Role`.

## Modelo

- Niveles: `0` sin acceso, `1` solo lectura, `2` crear y modificar.
- Un campo entero por módulo en `Role`: `customers`, `suppliers`, `materials`,
  `purchases`, `sales`, `inventory`, `accounting`, `reporting`.
- Un usuario puede tener varios roles (`UserRole`); el permiso efectivo por módulo es
  el **máximo** entre sus roles.
- `is_superuser` **no** da acceso a los módulos: un superusuario sin roles ve el
  dashboard vacío y es redirigido fuera de `/materials/`.
- Los roles se gestionan solo desde `/admin/`.

## Dónde se calcula: `users/permissions.py`

Toda la lógica vive en un único módulo:

| Función / constante | Qué hace |
| --- | --- |
| `MODULES` | Tupla con los nombres de los módulos (deben coincidir con los campos de `Role`) |
| `get_user_permissions(user)` | `dict` módulo → nivel máximo, en una sola consulta (`aggregate` con `Max` por módulo) |
| `get_module_permission(user, module)` | Nivel máximo para un módulo concreto |
| `get_user_roles(user)` | Lista de nombres de rol del usuario |

Las tres devuelven 0 / `{...: 0}` / `[]` si el usuario no está autenticado.

Quién lo usa:

- `core/context_processors.py` → `get_permissions` inyecta `permissions` y `roles` en
  **todas** las plantillas. `core.views.dashboard_view` ya no calcula nada; depende de
  este context processor.
- `materials/views.py` llama a `get_module_permission(request.user, 'materials')` en
  cada vista.

Para añadir un módulo nuevo: campo en `Role` + migración, nombre en `MODULES` y columna
en `RoleAdmin.list_display`.

## Cómo se aplica en `materials`

| Vista | 0 | 1 | 2 |
| --- | --- | --- | --- |
| `materials_list` | → `dashboard` | ver lista y exportar CSV | igual + botones de alta/edición/borrado |
| `material_create` | → `dashboard` | → lista de materiales | permitido |
| `material_edit` | → `dashboard` | → lista de materiales | permitido |
| `material_delete` | → lista de materiales | → lista de materiales | borra si es POST |

El permiso se comprueba **antes** de buscar el objeto, así que un usuario sin acceso
recibe la misma redirección exista o no el ID.

En plantillas: `{% if permissions.materials >= 2 %}` controla los botones de escritura y
`{% if permissions.<modulo> > 0 %}` las tarjetas del dashboard y el menú.
