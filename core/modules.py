"""Catálogo de módulos del portal: lo usan la navegación (base.html) y el dashboard.

- `key` debe coincidir con el campo del módulo en `users.models.Role`.
- `url_name` es None mientras el módulo no tenga pantallas.
- `status`: 'live' (disponible), 'building' (en construcción) o 'soon' (próximamente).
- `color` es el tono del módulo: usa la clase `tone-<color>` de core/static/css/portal.css.
- `icon` es el contenido interno de un <svg viewBox="0 0 24 24">.
"""

MODULE_CATALOG = [
    {
        'key': 'materials',
        'color': 'lime',
        'name': 'Materiales',
        'description': 'Catálogo de materiales, unidades y tipos, con exportación a CSV.',
        'url_name': 'materials:materials_list',
        'status': 'live',
        'icon': '<path d="m12 3 9 5-9 5-9-5 9-5Zm-9 9 9 5 9-5M3 16l9 5 9-5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" />',
    },
    {
        'key': 'suppliers',
        'color': 'lilac',
        'name': 'Proveedores',
        'description': 'Datos fiscales, contacto y condiciones de pago de cada proveedor.',
        'url_name': None,
        'status': 'building',
        'icon': '<path d="M3 7h11v11H3zM14 11h4l3 3v4h-7z" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" /><circle cx="7.5" cy="18.5" r="2" stroke="currentColor" stroke-width="1.7" /><circle cx="17.5" cy="18.5" r="2" stroke="currentColor" stroke-width="1.7" />',
    },
    {
        'key': 'customers',
        'color': 'sky',
        'name': 'Clientes',
        'description': 'Cartera de clientes y sus datos de contacto.',
        'url_name': None,
        'status': 'soon',
        'icon': '<path d="M16 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2m12-13a4 4 0 1 1-8 0 4 4 0 0 1 8 0Zm2 5a4 4 0 0 1 4 4v2" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" /><path d="M17 4a4 4 0 0 1 0 8" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" />',
    },
    {
        'key': 'purchases',
        'color': 'pink',
        'name': 'Compras',
        'description': 'Órdenes de compra a proveedores y su seguimiento.',
        'url_name': None,
        'status': 'soon',
        'icon': '<circle cx="9" cy="21" r="1" stroke="currentColor" stroke-width="1.7" /><circle cx="19" cy="21" r="1" stroke="currentColor" stroke-width="1.7" /><path d="M2 3h2l2.5 12.2a2 2 0 0 0 2 1.6h9.8a2 2 0 0 0 2-1.6L22 8H5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" />',
    },
    {
        'key': 'sales',
        'color': 'tangerine',
        'name': 'Ventas',
        'description': 'Pedidos y ventas a clientes.',
        'url_name': None,
        'status': 'soon',
        'icon': '<path d="m3 17 6-6 4 4 8-9m-6 0h6v6" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" />',
    },
    {
        'key': 'inventory',
        'color': 'sun',
        'name': 'Inventario',
        'description': 'Existencias y movimientos de almacén.',
        'url_name': None,
        'status': 'soon',
        'icon': '<path d="m12 3 9 5-9 5-9-5 9-5Zm-9 5v8l9 5 9-5V8m-9 5v8" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" />',
    },
    {
        'key': 'accounting',
        'color': 'mint',
        'name': 'Contabilidad',
        'description': 'Registro contable de las operaciones.',
        'url_name': None,
        'status': 'soon',
        'icon': '<path d="M5 3h14v18l-3-2-4 2-4-2-3 2V3Z" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" /><path d="M9 8h6m-6 4h6" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" />',
    },
    {
        'key': 'reporting',
        'color': 'coral',
        'name': 'Reportes',
        'description': 'Indicadores y reportes del negocio.',
        'url_name': None,
        'status': 'soon',
        'icon': '<path d="M4 19V5m0 14h17M8 15v-4m5 4V7m5 8v-6" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" />',
    },
]


def get_user_modules(permissions):
    """Módulos del catálogo a los que el usuario tiene acceso, con su nivel (1 o 2)."""
    return [
        {**module, 'level': permissions[module['key']]}
        for module in MODULE_CATALOG
        if permissions[module['key']] > 0
    ]
