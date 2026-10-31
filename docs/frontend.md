# Frontend

Diseño actual: **"Taller"** (2026-10-31). Papel crema con retícula de puntos, tinta
negra, bordes de 2 px, sombras sólidas desplazadas (estilo neo-brutalista) y un color
propio por módulo. Sustituye al tema oscuro del 2026-10-30.

## Plantillas

| Plantilla | Extiende | Uso |
| --- | --- | --- |
| `core/templates/core/_head.html` | — (parcial) | `<meta>`, script que aplica el acento guardado antes de pintar, Tailwind CDN, fuentes, `app.css` y `portal.css`. Lo incluyen `base.html` y el login |
| `core/templates/core/_accent_picker.html` | — (parcial) | Selector de color de acento (5 muestras) |
| `core/templates/core/base.html` | — | Barra superior flotante, menú móvil, mensajes, `{% block content %}` y pie |
| `core/templates/core/dashboard.html` | base | Saludo, cifras, módulos y materiales recientes |
| `users/templates/users/login.html` | — (HTML propio) | Login |
| `materials/templates/materials/materials_list.html` | base | Resumen, filtros, tabla / tarjetas, paginación, diálogo de borrado |
| `materials/templates/materials/material_form.html` | base | Alta y edición con etiqueta de almacén en vivo |
| `materials/templates/materials/_status.html` | — (parcial) | Etiqueta de estado de un material |
| `materials/templates/materials/_row_actions.html` | — (parcial) | Editar / eliminar de cada fila |

Bloques de `base.html`: `title` (se muestra como "<title> | ERP Project") y `content`.

## Sistema de diseño: `core/static/css/portal.css`

Todo el color sale de variables CSS; las plantillas usan clases semánticas y no
valores hexadecimales. Para cambiar la paleta basta con editar los tokens de `:root`.

### Tokens

| Variable | Valor | Uso |
| --- | --- | --- |
| `--paper` / `--paper-2` | `#f3eee3` / `#e8e0cf` | Fondo de página / fondos apagados |
| `--card` | `#fffdf8` | Tarjetas y campos |
| `--ink` / `--ink-2` / `--ink-3` | `#16130f` / `#4a443b` / `#6b6457` | Texto, bordes y sombras / texto secundario / pistas |
| `--lime`, `--lilac`, `--sky`, `--pink`, `--tangerine`, `--sun`, `--mint`, `--coral` | — | Colores de módulos y tarjetas |
| `--accent` | `--tangerine` por defecto | Color de acento elegido por el usuario |
| `--danger` | `#e5383b` | Botón de eliminar |
| `--shadow`, `--shadow-lg`, `--shadow-sm` | `4px` / `7px` / `2px` sólidas en `--ink` | Sombras |

Fuentes (Google Fonts): **Bricolage Grotesque** (`--font-display`, títulos),
**Instrument Sans** (`--font-body`) y **JetBrains Mono** (`--font-mono`, códigos y
etiquetas).

### Clases principales

- **Tonos:** `tone-lime`, `tone-lilac`, `tone-sky`, `tone-pink`, `tone-tangerine`,
  `tone-sun`, `tone-mint`, `tone-coral`, `tone-accent`, `tone-card`, `tone-paper`,
  `tone-ink`. Están **al final del archivo** para ganar a los fondos de los
  componentes; no moverlas.
- **Texto:** `portal-display` (títulos grandes), `portal-eyebrow` (rótulo mono con
  punto de acento), `portal-marker` (subrayado de rotulador con el acento),
  `portal-muted`, `portal-subtle`.
- **Superficies:** `portal-card` (+ `portal-card--lift` para elevar al pasar el
  cursor), `portal-sticker` (etiqueta tipo pegatina), `portal-reveal` (entrada con
  `--delay`).
- **Navegación:** `portal-topbar`, `portal-brand`, `portal-navpill`, `portal-dot`,
  `portal-avatar`, `portal-icon-button`, `portal-swatches` / `portal-swatch`,
  `portal-sheet` (menú móvil), `portal-scrim`.
- **Datos:** `portal-stat` (+ `__value`, `__label`, `__icon`), `portal-meter` (barra
  rayada con el acento), `portal-module` (+ `__icon`, `__name`, `__arrow`,
  `--soon` con rayado de "en obra"), `portal-badge` (+ `--ink`, `--building`),
  `portal-status--active|inactive|other`, `portal-code`, `portal-table`,
  `portal-page-link`.
- **Formularios:** `portal-label`, `portal-field`, `portal-field-wrap` (campo con
  icono), `portal-segmented`, `portal-field-error`, `portal-hint`, `portal-filter-chip`.
- **Botones:** `portal-button` (tinta; al pasar el cursor toma el acento),
  `portal-button-secondary`, `portal-button-danger`, `portal-icon-action`
  (+ `--danger`).
- **Otros:** `portal-alert--success|warning|error`, `portal-dialog`, `portal-ticket`
  (+ `__hole`, `__tear`) y `portal-barcode` para la etiqueta de almacén,
  `portal-marquee` (cinta en movimiento), `portal-spin` (sello giratorio).

`app.css` conserva la base heredada; de él solo se usan `ui-skip-link`,
`ui-loading-spinner` y la regla global de `prefers-reduced-motion`, que desactiva
todas las animaciones.

### Color de acento

El usuario elige entre mandarina, lila, lima, cielo y rosa desde la barra superior,
el menú móvil o el login. `script.js` guarda la elección en `localStorage`
(`erp-accent`) y pone `data-accent` en `<html>`; `_head.html` lo aplica antes de pintar.
Es una preferencia por navegador, no se guarda en el servidor.

## JavaScript: `core/static/js/script.js`

Va dentro de un bloque `{ ... }` para que sus constantes no choquen con las de
`users/js/login.js`.

- Selector de acento (`[data-accent-option]`).
- Menú móvil (`#menu-toggle`, `#portal-sheet`, `#sheet-scrim`, `[data-sheet-close]`;
  cierra con Escape, clic fuera o al pasar a escritorio).
- Confirmación con `<dialog id="confirm-dialog">` para `form[data-confirm="<nombre>"]`.
  Si el navegador no soporta `<dialog>`, el formulario se envía sin confirmar.
- Vista previa en vivo y contador de caracteres en `[data-material-form]`
  (`data-preview-source` en los campos → `data-preview` en la etiqueta; `data-empty`
  es el texto cuando el campo está vacío).
- Estado de carga en `form[data-loading-form]` (se salta si otro listener canceló el
  envío).

## Estructura de `base.html`

- **Barra superior flotante** (píldora): logo, "Inicio" y los módulos disponibles del
  usuario (con su punto de color), selector de acento, avatar con nombre y roles, y
  botón de cerrar sesión (formulario POST). El enlace activo se marca comparando
  `request.resolver_match.namespace` con la clave del módulo.
- **Menú móvil** (`< lg`): panel que baja desde arriba con todos los módulos del
  usuario; los que no tienen pantallas aparecen con borde punteado y "En obra" o
  "Pronto".
- **Pie:** año y fecha actual.

## Catálogo de módulos: `core/modules.py`

`MODULE_CATALOG` define para cada módulo `key` (= campo de `Role`), `color` (sufijo de
la clase `tone-*`), `name`, `description`, `url_name` (o `None`), `status` (`live` /
`building` / `soon`) e `icon` (contenido interno de un `<svg viewBox="0 0 24 24">`).
`get_user_modules()` devuelve los que el usuario puede ver con su `level`; el context
processor lo expone como `user_modules`.

| Módulo | Color |
| --- | --- |
| Materiales | lima |
| Proveedores | lila |
| Clientes | cielo |
| Compras | rosa |
| Ventas | mandarina |
| Inventario | sol |
| Contabilidad | menta |
| Reportes | coral |

Cuando un módulo tenga pantallas: poner su `url_name`, cambiar `status` a `live` y
usar `app_name = '<key>'` en su `urls.py`.

## Dashboard

Datos reales, sin cifras inventadas:

- Saludo grande en el color de acento, con los roles como pegatinas y un sello
  giratorio decorativo.
- Cifras: módulos con acceso (`readable_count` / `module_total`), con escritura
  (`writable_count`) y, si el usuario ve materiales, total y activos
  (`materials_summary`). Si no, número de roles.
- "Tus módulos": los disponibles en su color y con flecha; los demás en blanco con
  rayado y borde punteado.
- "Lo último": los 5 materiales más recientes.

## Login

- `users/templates/users/login.html`, `users/static/users/css/login.css` (mosaico de
  módulos, botón de mostrar contraseña, aviso de Bloq Mayús) y
  `users/static/users/js/login.js` (mostrar contraseña y Bloq Mayús).
- Titular con "lugar." subrayado con el acento, mosaico decorativo (`aria-hidden`) con
  el estado real de cada módulo (actualizarlo a mano si cambia), tarjeta con el
  formulario, selector de color y cinta inferior con los módulos.
- Errores: solo `form.non_field_errors` y los errores de campo; el mensaje de
  credenciales inválidas está en `LoginForm.error_messages['invalid_login']`.

## Materiales

### Lista (`materials_list.html`)

- Título con subrayado de acento, "Exportar CSV" (respeta los filtros) y "Crear
  material" (solo nivel 2).
- Resumen del catálogo completo, sin filtros (`summary`): total, activos, inactivos y
  tipos.
- Filtros con icono; botón de limpiar solo si hay filtros (`has_filters`). Cada filtro
  activo es una etiqueta con ✕ que lo quita con `{% querystring <campo>=None page=None %}`.
- Tabla con cabecera en tinta (`md` o más); en móvil, lista de tarjetas.
- Eliminar abre el diálogo de confirmación.

### Formulario (`material_form.html`)

- Campos escritos a mano (no `{{ form.campo }}`) para controlar clases, `aria-*`,
  `maxlength` y `required`.
- Unidad con sugerencias fijas (`<datalist id="unit-options">`) y tipo con los tipos
  existentes (`material_types`, que envían `material_create` y `material_edit`).
- Estado como interruptor Activo / Inactivo; al crear, la vista pone
  `initial={'status': 'Active'}`.
- Columna derecha: **etiqueta de almacén** en el color de acento (agujero, línea de
  corte, código de barras decorativo) que se actualiza al escribir y, al editar,
  creador y fechas.
- Las fechas se muestran en UTC (`TIME_ZONE = 'UTC'`).
