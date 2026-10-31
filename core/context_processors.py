from users.permissions import get_user_permissions, get_user_roles
from .modules import get_user_modules

def get_permissions(request):
  permissions = get_user_permissions(request.user)
  return {
    'permissions': permissions,
    'roles': get_user_roles(request.user),
    'user_modules': get_user_modules(permissions),
  }
