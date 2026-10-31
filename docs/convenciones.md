# Convenciones y patrón de módulos

## Estilo de código observado

- Código, modelos y nombres de campos en **inglés**; textos de UI y mensajes
  (`messages.success`) en **español**.
- Vistas basadas en funciones con `@login_required`; no hay class-based views.
- Indentación mixta: `users/` y `core/views.py` usan 4 espacios; `materials/views.py`,
  `materials/forms.py`, `*/urls.py` y `core/context_processors.py` usan 2. Respetar la
  del archivo que se edite.
- Código de negocio separado del PK: `id_material` / `id_supplier` (CharField único),
  mientras las URLs usan el `pk` numérico.
- Auditoría simple en cada modelo de negocio: `created_at`, `updated_at`, `created_by`.
- `status` como texto `Active` / `Inactive`.
- Commits con gitmoji (`:sparkles:`, `:memo:`, `:tada:`) y mensaje en español.

## Receta para un módulo nuevo (basada en `materials`)

1. `python manage.py startapp <modulo>` y añadirlo a `INSTALLED_APPS`.
2. Modelo con código de negocio único, campos de auditoría y `class Meta` (bien
   escrito) con `verbose_name`.
3. `ModelForm` en `forms.py` con los campos editables (sin `created_by`).
4. `urls.py` con `app_name = '<modulo>'` y rutas `''`, `create/`, `<int:pk>/edit/`,
   `<int:pk>/delete/`.
5. Vistas: lista (filtros por GET, `Paginator` de 10 sobre un queryset ordenado —
   `ordering` en `Meta`,
   `?export=csv` con BOM UTF-8, enlaces con `{% querystring %}`),
   crear (asigna `created_by = request.user`), editar, borrar solo por POST. Validar el
   permiso del módulo **antes** de cargar el objeto.
6. Plantillas en `<modulo>/templates/<modulo>/` extendiendo `core/base.html` y usando
   las clases `ui-*` de `app.css` y `data-loading-form`.
7. Incluir las URLs en `erp_project/urls.py`.
8. Enlazar la tarjeta del dashboard (`core/templates/core/dashboard.html`) y añadir la
   entrada al menú de `base.html` condicionada a `permissions.<modulo> > 0`.
9. Si el módulo es nuevo en `Role`: añadir el campo, su nombre en
   `users.permissions.MODULES` y en `RoleAdmin.list_display`, y migrar. En las vistas,
   validar con `get_module_permission(request.user, '<modulo>')`.
10. Registrar el modelo en `admin.py` (hoy `materials` no lo está).
11. `makemigrations` + `migrate`, y añadir pruebas de permisos (0/1/2) y CRUD en
    `<modulo>/tests.py`, siguiendo `materials/tests.py`.

## Pruebas

`python manage.py test` (25 pruebas, base de datos temporal):

| Archivo | Cubre |
| --- | --- |
| `users/tests.py` | `users/permissions.py` (máximo entre roles, superusuario sin roles), login, redirección de anónimos, logout solo por POST, búsqueda de roles en el admin |
| `core/tests.py` | Dashboard: módulos y roles según permisos, logout como formulario POST |
| `materials/tests.py` | Niveles 0/1/2 en las cuatro vistas, alta con `created_by`, edición, borrado solo por POST, filtro por tipo, paginación ordenada con filtros codificados, CSV filtrado, `__str__` |
