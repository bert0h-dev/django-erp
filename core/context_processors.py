from users.permissions import get_user_permissions, get_user_roles

def get_permissions(request):
  return {
    'permissions': get_user_permissions(request.user),
    'roles': get_user_roles(request.user),
  }
