import csv
import io

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction

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

@login_required
def supplier_bulk_create(request):
  max_permission = get_module_permission(request.user, 'suppliers')

  if max_permission < 2:
      return redirect('suppliers:suppliers_list')

  if request.method == 'POST':
    form = CsvUploadForm(request.POST, request.FILES)
    if form.is_valid():
      csv_file = form.cleaned_data['csv_file']
      try:
        data_set = csv_file.read().decode('UTF-8')
      except UnicodeDecodeError:
        try:
          csv_file.seek(0)
          data_set = csv_file.read().decode('ISO-8859-1')
        except Exception as e:
          return render(request, 'suppliers/supplier_bulk_upload.html', {'form': form, 'error_message': f'Error al leer el archivo CSV: {str(e)}'})

      io_string = io.StringIO(data_set)
      reader = csv.DictReader(io_string)

      if reader.fieldnames:
        if reader.fieldnames[0].startswith('\ufeff'):
          reader.fieldnames[0] = reader.fieldnames[0].lstrip('\ufeff')

        cleaned_fieldnames = [key.strip().lower() for key in reader.fieldnames]
        reader.fieldnames = cleaned_fieldnames

      successful_records = []
      error_records = []
      suppliers_to_create = []
      # Fila donde apareció cada id_supplier: la validación del formulario solo compara contra la base de datos
      seen_ids = {}

      for i, row in enumerate(reader):
        row_number = i + 2
        form_data = {}

        for key, value in row.items():
          cleaned_value = value.strip() if isinstance(value, str) else value
          form_data[key] = cleaned_value

        supplier_form = SupplierForm(form_data)

        if supplier_form.is_valid():
          id_supplier = supplier_form.cleaned_data['id_supplier']
          if id_supplier in seen_ids:
            error_records.append({
              'row': row_number,
              'data': form_data,
              'errors': {'id_supplier': f'Está repetido en el archivo (ya aparece en la fila {seen_ids[id_supplier]}).'},
            })
            continue

          seen_ids[id_supplier] = row_number
          supplier = supplier_form.save(commit=False)
          supplier.created_by = request.user
          suppliers_to_create.append(supplier)
          successful_records.append({'row': row_number, 'data': form_data})
        else:
          errors = {
            field: ', '.join(err)
            for field, err in supplier_form.errors.items()
          }
          error_records.append({'row': row_number, 'data': form_data, 'errors': errors})

      if suppliers_to_create:
        try:
          with transaction.atomic():
            Suppliers.objects.bulk_create(suppliers_to_create)
        except IntegrityError:
          # Otro usuario registró alguno de estos ID mientras se procesaba el archivo
          return render(request, 'suppliers/supplier_bulk_upload.html', {
            'form': form,
            'error_message': 'Algunos ID de proveedor ya existen. No se registró ningún proveedor; vuelve a subir el archivo.',
          })

      if successful_records:
        count = len(successful_records)
        messages.success(request, 'Se registró 1 proveedor.' if count == 1 else f'Se registraron {count} proveedores.')
      if error_records:
        count = len(error_records)
        messages.warning(request, '1 fila tiene errores y no se registró.' if count == 1 else f'{count} filas tienen errores y no se registraron.')

      context = {
        'form': form,
        'successful_count': len(successful_records),
        'error_count': len(error_records),
        'total_rows': len(successful_records) + len(error_records),
        'error_records': error_records,
        'successful_records': successful_records,
        'report_generated': True,
      }

      return render(request, 'suppliers/supplier_bulk_upload.html', context)
    
    return render(request, 'suppliers/supplier_bulk_upload.html', {'form': form})
  
  else:
    form = CsvUploadForm()
    return render(request, 'suppliers/supplier_bulk_upload.html', {'form': form})

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