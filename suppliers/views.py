from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Suppliers
from .forms import SupplierForm
from django.core.paginator import Paginator
from django.http import HttpResponse
import csv
from users.permissions import get_module_permission

def get_supplier_values(field):
  """Valores distintos ya registrados en un campo (para filtros y sugerencias)."""
  return (
    Suppliers.objects.exclude(**{field: ''})
    .order_by(field)
    .values_list(field, flat=True)
    .distinct()
  )

@login_required
def suppliers_list(request):
  max_permission = get_module_permission(request.user, 'suppliers')

  if max_permission == 0:
    return redirect('dashboard')

  suppliers_list = Suppliers.objects.select_related('created_by')

  id_supplier = request.GET.get('id_supplier')
  name = request.GET.get('name')
  country = request.GET.get('country')
  status = request.GET.get('status')

  if id_supplier:
    suppliers_list = suppliers_list.filter(id_supplier__icontains=id_supplier)
  if name:
    suppliers_list = suppliers_list.filter(name__icontains=name)
  if country:
    suppliers_list = suppliers_list.filter(country=country)
  if status is not None and status != '':
    suppliers_list = suppliers_list.filter(status=status)

  if request.GET.get('export') == "csv":
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="suppliers.csv"'

    response.write('\ufeff'.encode('utf-8'))
    writer = csv.writer(response)

    writer.writerow(['ID Proveedor', 'Nombre Legal', 'Nombre', 'ID Fiscal', 'País', 'Estado/Provincia', 'Ciudad', 'Dirección', 'Código Postal', 'Teléfono', 'Email', 'Nombre de Contacto', 'Rol de Contacto', 'Categoría', 'Términos de Pago', 'Moneda', 'Método de Pago', 'Cuenta Bancaria', 'Status', 'Creado Por', 'Creado En', 'Actualizado En'])

    for supplier in suppliers_list:
      writer.writerow([
        supplier.id_supplier,
        supplier.legal_name,
        supplier.name,
        supplier.tax_id,
        supplier.country,
        supplier.state_province,
        supplier.city,
        supplier.address,
        supplier.zip_code,
        supplier.phone,
        supplier.email,
        supplier.contact_name,
        supplier.contact_role,
        supplier.category,
        supplier.payment_terms,
        supplier.currency,
        supplier.payment_method,
        supplier.bank_account,
        supplier.status,
        supplier.created_by.username if supplier.created_by else 'N/A',
        supplier.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        supplier.updated_at.strftime('%Y-%m-%d %H:%M:%S')
      ])
    return response

  
  paginator = Paginator(suppliers_list, 10)
  page_number = request.GET.get('page')
  page_obj = paginator.get_page(page_number)

  all_suppliers = Suppliers.objects.all()

  context = {
    'page_obj': page_obj,
    'all_countries': get_supplier_values('country'),
    'has_filters': any([id_supplier, name, country, status]),
    'summary': {
      'total': all_suppliers.count(),
      'active': all_suppliers.filter(status='Active').count(),
      'inactive': all_suppliers.filter(status='Inactive').count(),
      'countries': get_supplier_values('country').count(),
    },
  }

  return render(request, 'suppliers/suppliers_list.html', context)

@login_required
def supplier_create(request):
  max_permission = get_module_permission(request.user, 'suppliers')

  if max_permission == 1:
    return redirect('suppliers:suppliers_list')
  if max_permission == 0:
    return redirect('dashboard')
  
  if request.method == 'POST':
    form = SupplierForm(request.POST)
    if form.is_valid():
      supplier = form.save(commit=False)
      supplier.created_by = request.user
      supplier.save()

      messages.success(request, 'El proveedor se creó correctamente.')
      return redirect('suppliers:suppliers_list')
  else:
    form = SupplierForm(initial={'status': 'Active'})

  context = {
    'form': form,
    'categories': get_supplier_values('category'),
  }

  return render(request, 'suppliers/supplier_form.html', context)

@login_required
def supplier_edit(request,pk):
  max_permission = get_module_permission(request.user, 'suppliers')

  if max_permission == 1:
    return redirect('suppliers:suppliers_list')
  if max_permission == 0:
    return redirect('dashboard')

  supplier = get_object_or_404(Suppliers, pk=pk)

  if request.method == 'POST':
    form = SupplierForm(request.POST, instance=supplier)
    if form.is_valid():
      form.save()
      messages.success(request, 'Los cambios del proveedor se guardaron correctamente.')
      return redirect('suppliers:suppliers_list')
  else:
    form = SupplierForm(instance=supplier)
    
  context = {
    'form': form,
    'supplier': supplier,
    'categories': get_supplier_values('category'),
  }

  return render(request, 'suppliers/supplier_form.html', context)

@login_required
def supplier_delete(request, pk):
  max_permission = get_module_permission(request.user, 'suppliers')

  if max_permission < 2:
    return redirect('suppliers:suppliers_list')

  supplier = get_object_or_404(Suppliers, pk=pk)

  if request.method == 'POST':
    supplier.delete()
    messages.success(request, 'El proveedor se eliminó correctamente.')
    return redirect('suppliers:suppliers_list')

  return redirect('suppliers:suppliers_list')