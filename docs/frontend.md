# Frontend

## Plantillas

| Plantilla | Extiende | Uso |
| --- | --- | --- |
| `core/templates/core/base.html` | — | Layout: header teal, menú de usuario, menú móvil, mensajes, `{% block content %}`. "Cerrar sesión" es un `<form method="post">` con CSRF en ambos menús |
| `core/templates/core/dashboard.html` | base | Tarjetas de módulos según `permissions` |
| `users/templates/users/login.html` | — (HTML propio) | Pantalla de login |
| `materials/templates/materials/materials_list.html` | base | Filtros, chips de filtros activos, tabla, paginación, export CSV |
| `materials/templates/materials/material_form.html` | base | Alta y edición (cambia textos si existe `material`) |

Bloques de `base.html`: `title` y `content`.

En el dashboard solo la tarjeta de **Materiales** enlaza a una ruta real; las demás
(Clientes, Proveedores, Compras, Ventas, Inventario, Contabilidad, Reportes) usan
`href="#"`. El menú de `base.html` solo tiene Dashboard, Materiales y Cerrar sesión.

## Estilos

- Color principal `#106573`; hover `#0c535e`; fondo `#f2f6f6`; acentos `#e8f3f3`,
  `#b8d7d9`.
- Tailwind por CDN (JIT en el navegador; requiere Internet, no apto para producción).
- `core/static/css/app.css` define componentes reutilizables: `ui-field`,
  `ui-button-primary`, `ui-button-secondary`, `ui-button-danger`, `ui-status-error`,
  `ui-loading-spinner`, `ui-skip-link`, entre otros. Usarlos en vez de repetir clases.
- Accesibilidad cuidada: skip links, `aria-expanded`, `aria-invalid`,
  `aria-describedby`, `role="alert"`.

## JavaScript (`core/static/js/script.js`)

- Menú hamburguesa (`#hamburger-btn` / `#mobile-menu`), cierra con Escape.
- Menú de usuario (`#user-menu-button` / `#user-menu-dropdown`), cierra con Escape o
  clic fuera.
- Formularios con atributo `data-loading-form`: al enviar deshabilitan el botón submit,
  ponen `aria-busy`, cambian el texto de `[data-submit-label]` por
  `data-loading-label` y muestran `.ui-loading-spinner`.

## Patrón de formularios

`material_form.html` renderiza cada campo a mano (`<input name="{{ form.x.html_name }}"
value="{{ form.x.value|default:'' }}">`) en lugar de `{{ form.x }}`. Consecuencias:

- Los atributos que Django pondría (`maxlength`, `required`) no se aplican.
- `status` es un `<select>` con `Active`/`Inactive` en HTML, pero el modelo acepta
  cualquier texto.

## Detalles de la lista de materiales

- El select de "Tipo de material" itera `all_material_types`: lista de valores
  distintos de `material_type` que envía la vista. El filtro por tipo es exacto.
- Los enlaces de paginación y de export CSV usan la etiqueta `{% querystring %}`
  (Django ≥ 5.1), que conserva y codifica los filtros actuales:
  `{% querystring page=i %}`, `{% querystring export='csv' page=None %}`.
- Al final del formulario hay `<input type="hidden" name="{{ form.created_by_id.html_name }}">`;
  ese campo no existe en `MaterialForm`, así que genera un input sin nombre que no hace
  nada. `created_by` se asigna correctamente en la vista.
