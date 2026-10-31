from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from materials.models import Material
from users.permissions import get_user_permissions
from .modules import MODULE_CATALOG

@login_required
def dashboard_view(request):
    # `permissions`, `roles` y `user_modules` llegan a la plantilla desde core.context_processors.get_permissions
    permissions = get_user_permissions(request.user)

    context = {
        'module_total': len(MODULE_CATALOG),
        'readable_count': sum(1 for level in permissions.values() if level > 0),
        'writable_count': sum(1 for level in permissions.values() if level == 2),
    }

    if permissions['materials'] > 0:
        context['materials_summary'] = {
            'total': Material.objects.count(),
            'active': Material.objects.filter(status='Active').count(),
            'recent': Material.objects.select_related('created_by')[:5],
        }

    return render(request, 'core/dashboard.html', context)
