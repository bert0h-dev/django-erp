from django.db.models import Max

from .models import UserRole

MODULES = (
    'customers',
    'suppliers',
    'materials',
    'purchases',
    'sales',
    'inventory',
    'accounting',
    'reporting',
)


def get_user_permissions(user):
    """Devuelve el nivel máximo (0, 1 o 2) por módulo entre todos los roles del usuario."""
    permissions = dict.fromkeys(MODULES, 0)

    if not user.is_authenticated:
        return permissions

    levels = UserRole.objects.filter(user_id=user).aggregate(
        **{module: Max(f'role__{module}') for module in MODULES}
    )
    for module, level in levels.items():
        permissions[module] = level or 0

    return permissions


def get_module_permission(user, module):
    """Devuelve el nivel máximo (0, 1 o 2) del usuario para un módulo."""
    if not user.is_authenticated:
        return 0

    return UserRole.objects.filter(user_id=user).aggregate(
        level=Max(f'role__{module}')
    )['level'] or 0


def get_user_roles(user):
    if not user.is_authenticated:
        return []

    return list(
        UserRole.objects.filter(user_id=user).values_list('role__role_name', flat=True)
    )
