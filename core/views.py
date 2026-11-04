from collections import Counter
from datetime import date
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.utils import timezone
from materials.models import Material, MaterialType
from suppliers.models import Suppliers
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

    if permissions.get('materials', 0) > 0:
        total = Material.objects.count()
        
        context['materials_summary'] = {
            'total': total,
            'active': Material.objects.filter(status__is_active=True).count(),
            'recent': Material.objects.select_related('created_by', 'material_type', 'status')[:5],
        }

    if permissions.get('suppliers', 0) > 0:
        total = Suppliers.objects.count()
        countries = (
            Suppliers.objects.values('country__name')
            .annotate(count=Count('id'))
            .order_by('-count', 'country__name')[:4]
        )
        context['suppliers_summary'] = {
            'total': total,
            'active': Suppliers.objects.filter(status__is_active=True).count(),
            'recent': Suppliers.objects.select_related('created_by', 'status', 'country')[:5],
            'countries': [
                {'name': row['country__name'], 'count': row['count'], 'share': round(row['count'] * 100 / total)}
                for row in countries
            ],
        }

    return render(request, 'core/dashboard.html', context)
