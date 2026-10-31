from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
    # `permissions` y `roles` llegan a la plantilla desde core.context_processors.get_permissions
    return render(request, 'core/dashboard.html')
