# Modelos y base de datos

## `users`

### `User(AbstractUser)` — tabla `users`

- PK propia: `user_id = AutoField(primary_key=True)` (no existe `id`).
- Redefine `username` (unique, 150) y `password` (128), igual que `AbstractUser`.
- Resto de campos heredados: `first_name`, `last_name`, `email`, `is_staff`,
  `is_active`, `is_superuser`, `date_joined`, `last_login`, `groups`,
  `user_permissions`.

### `Role` — tabla `roles`

- PK: `role_name = CharField(max_length=50, primary_key=True)`. Renombrar un rol
  cambia su PK.
- Un `IntegerField` por módulo con `choices` 0/1/2, default 0: `customers`,
  `suppliers`, `materials`, `purchases`, `sales`, `inventory`, `accounting`,
  `reporting`.

### `UserRole` — tabla `user_roles`

- `user_id = ForeignKey(User)` (ojo: el campo se llama `user_id`, así que la columna
  en BD es `user_id_id` y el filtro es `UserRole.objects.filter(user_id=...)`).
- `role = ForeignKey(Role)`.
- `unique_together = ('user_id', 'role')`.

Migración: `users/migrations/0001_initial.py`.

## `materials`

### `Material` — tabla `materials_material` (por defecto)

| Campo | Tipo | Notas |
| --- | --- | --- |
| `id` | BigAutoField | PK usada en las URLs |
| `id_material` | CharField(50) | `null=True`, `unique=True`; código de negocio |
| `name` | CharField(100) | `blank=True` |
| `description` | TextField | `max_length=250` (solo se valida en formularios), `blank=True` |
| `unit` | CharField(50) | texto libre |
| `material_type` | CharField(50) | texto libre |
| `status` | CharField(50) | la UI usa `Active` / `Inactive` |
| `created_at` / `updated_at` | DateTimeField | auto |
| `created_by` | FK a User | `SET_NULL`, se asigna en la vista de alta |

`class Meta` define `verbose_name`, `verbose_name_plural` y
`ordering = ['-created_at', '-id']` (más recientes primero; necesario para que la
paginación sea estable). `__str__` devuelve `name`, o `id_material`, o `Material <pk>`.

Migraciones: `0001_initial.py`, `0002_alter_material_id_material.py`,
`0003_alter_material_options.py`, `0004_alter_material_options.py`.

## `suppliers` (sin migración)

### `Suppliers` — tabla futura `suppliers_suppliers`

Campos: `id_supplier` (CharField 50, null, unique), `legal_name`, `name`, `tax_id`,
`country`, `state_province`, `city`, `address`, `zip_code` (**IntegerField**),
`phone` (**IntegerField**), `email`, `contact_name`, `contact_role`, `category`,
`payment_terms`, `currency`, `payment_method`, `bank_account`, `status`,
`created_at`, `updated_at`, `created_by`.

Pendientes de diseño antes de migrar:

- `zip_code` y `phone` como enteros pierden ceros a la izquierda, `+`, espacios y
  extensiones; conviene `CharField`.
- El nombre del modelo está en plural (`Suppliers`); la convención Django es singular
  (`Supplier`), como `Material`.

## Datos actuales en `db.sqlite3` (2026-10-30)

| Tabla | Contenido |
| --- | --- |
| `roles` | `Administrator` (2 en todos los módulos), `Sales Representative` (customers 2, suppliers 0, materials 1, …) |
| `users` | 2 usuarios |
| `materials_material` | 1 material |

Todas las migraciones existentes están aplicadas.
