from collections import Counter
from datetime import date

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.utils import timezone
from materials.models import Material
from users.permissions import get_user_permissions
from .modules import MODULE_CATALOG

MONTH_LABELS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

# Lienzo de la gráfica (coincide con el viewBox del SVG en dashboard.html)
CHART_WIDTH = 600
CHART_HEIGHT = 200
CHART_PADDING = 16


def get_monthly_chart(months=6):
    """Materiales registrados por mes en los últimos `months` meses, listos para dibujar en SVG."""
    today = timezone.localdate()
    month_starts = []
    year, month = today.year, today.month
    for _ in range(months):
        month_starts.append(date(year, month, 1))
        year, month = (year, month - 1) if month > 1 else (year - 1, 12)
    month_starts.reverse()

    counts = Counter(
        (timezone.localtime(created_at).year, timezone.localtime(created_at).month)
        for created_at in Material.objects.filter(created_at__date__gte=month_starts[0]).values_list('created_at', flat=True)
    )
    values = [counts[(start.year, start.month)] for start in month_starts]
    peak = max(values) or 1

    step = (CHART_WIDTH - CHART_PADDING * 2) / (months - 1)
    points = []
    for index, (start, value) in enumerate(zip(month_starts, values)):
        points.append({
            'x': round(CHART_PADDING + step * index, 1),
            'y': round(CHART_HEIGHT - CHART_PADDING - (CHART_HEIGHT - CHART_PADDING * 2) * value / peak, 1),
            'value': value,
            'label': MONTH_LABELS[start.month - 1],
        })

    # Curva suave: cada tramo es una Bézier con los controles a la mitad del tramo
    line = f"M{points[0]['x']},{points[0]['y']}"
    for previous, current in zip(points, points[1:]):
        middle = round((previous['x'] + current['x']) / 2, 1)
        line += f" C{middle},{previous['y']} {middle},{current['y']} {current['x']},{current['y']}"
    area = f"{line} L{points[-1]['x']},{CHART_HEIGHT} L{points[0]['x']},{CHART_HEIGHT} Z"

    current, previous = values[-1], values[-2]
    return {
        'points': points,
        'line': line,
        'area': area,
        'total': sum(values),
        'current': current,
        'change': current - previous,
        'last': points[-1],
    }


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
        total = Material.objects.count()
        types = (
            Material.objects.exclude(material_type='')
            .values('material_type')
            .annotate(count=Count('id'))
            .order_by('-count', 'material_type')[:4]
        )
        context['materials_summary'] = {
            'total': total,
            'active': Material.objects.filter(status='Active').count(),
            'recent': Material.objects.select_related('created_by')[:5],
            'types': [
                {'name': row['material_type'], 'count': row['count'], 'share': round(row['count'] * 100 / total)}
                for row in types
            ],
            'chart': get_monthly_chart(),
        }

    return render(request, 'core/dashboard.html', context)
