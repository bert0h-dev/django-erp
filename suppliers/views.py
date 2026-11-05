import csv

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.paginator import Paginator

from core.bulk import catalog_lookup, process_bulk_upload, status_lookup
from core.models import Country, Status
from .models import Suppliers
from .forms import SupplierForm, CsvUploadForm
from users.permissions import get_module_permission

def get_supplier_values(field):
  """Valores distintos ya registrados en un campo (para filtros y sugerencias)."""
  return (
    Suppliers.objects.exclude(**{field: ''})
    .order_by(field)
    .values_list(field, flat=True)
    .distinct()
  )

def get_supplier_countries():
  """Países del catálogo que tienen al menos un proveedor (para el resumen)."""
  return Country.objects.filter(suppliers__isnull=False).distinct().order_by('name')

@login_required
def suppliers_list(request):
  max_permission = get_module_permission(request.user, 'suppliers')

  if max_permission == 0:
    return redirect('dashboard')

  suppliers_list = Suppliers.objects.select_related('created_by', 'status', 'country')

  id_supplier = request.GET.get('id_supplier')
  name = request.GET.get('name')
  country = request.GET.get('country')
  status = request.GET.get('status')

  if id_supplier:
    suppliers_list = suppliers_list.filter(id_supplier__icontains=id_supplier)
  if name:
    suppliers_list = suppliers_list.filter(name__icontains=name)
  if country:
    suppliers_list = suppliers_list.filter(country__abbreviation__iexact=country)
  if status is not None and status != '':
    suppliers_list = suppliers_list.filter(status__name__iexact=status)

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
        supplier.country.abbreviation if supplier.country else '',
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
        supplier.status.name if supplier.status else '',
        f"{supplier.created_by.first_name} {supplier.created_by.last_name}" if supplier.created_by else '',
        supplier.created_at.strftime('%Y-%m-%d %H:%M:%S') if supplier.created_at else '',
        supplier.updated_at.strftime('%Y-%m-%d %H:%M:%S') if supplier.updated_at else '',
      ])
    return response

  
  paginator = Paginator(suppliers_list, 10)
  page_number = request.GET.get('page')
  page_obj = paginator.get_page(page_number)

  all_suppliers = Suppliers.objects.all()

  context = {
    'page_obj': page_obj,
    'all_countries': Country.objects.order_by('name'),
    'all_status': Status.objects.order_by('name'),
    'has_filters': any([id_supplier, name, country, status]),
    'summary': {
      'total': all_suppliers.count(),
      'active': all_suppliers.filter(status__is_active=True).count(),
      'inactive': all_suppliers.filter(status__is_active=False).count(),
      'countries': get_supplier_countries().count(),
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
    form = SupplierForm()

  context = {
    'form': form,
    'categories': get_supplier_values('category'),
    'all_status': Status.objects.order_by('name'),
    'all_countries': Country.objects.order_by('name'),
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
    'all_status': Status.objects.order_by('name'),
    'all_countries': Country.objects.order_by('name'),
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

@login_required
def supplier_bulk_create(request):
  max_permission = get_module_permission(request.user, 'suppliers')

  if max_permission < 2:
    return redirect('suppliers:suppliers_list')

  context = {}

  if request.method == 'POST':
    form = CsvUploadForm(request.POST, request.FILES)
    if form.is_valid():
      context = process_bulk_upload(
        request,
        form.cleaned_data['csv_file'],
        form_class=SupplierForm,
        model=Suppliers,
        id_field='id_supplier',
        # El país se puede escribir por nombre, abreviación o como lo exporta el listado ("México", "MX" o "México (MX)")
        catalogs={
          'country': catalog_lookup(Country.objects.all(), 'name', 'abbreviation', str),
          'status': status_lookup(),
        },
        nouns=('proveedor', 'proveedores'),
      )
  else:
    form = CsvUploadForm()

  context.update({'form': form, 'all_status': Status.objects.order_by('name'), 'all_countries': Country.objects.order_by('name')})
  return render(request, 'suppliers/supplier_bulk_upload.html', context)

@login_required
def download_template_suppliers(request):
  max_permission = get_module_permission(request.user, 'suppliers')

  if max_permission < 2:
    return redirect('suppliers:suppliers_list')

  response = HttpResponse(content_type='text/csv')
  response['Content-Disposition'] = 'attachment; filename="supplier_template.csv"'

  writer = csv.writer(response)
  writer.writerow(['id_supplier', 'legal_name', 'name', 'tax_id', 'country', 'state_province', 'city', 'address', 'zip_code', 'phone', 'email', 'contact_name', 'contact_role', 'category', 'payment_terms', 'currency', 'payment_method', 'bank_account', 'status'])

  return response