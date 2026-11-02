from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Material
from .forms import MaterialForm, CsvUploadForm
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.http import HttpResponse
import csv
import io
from users.permissions import get_module_permission

def get_material_types():
  return (
    Material.objects.exclude(material_type='')
    .order_by('material_type')
    .values_list('material_type', flat=True)
    .distinct()
  )

@login_required
def materials_list(request):
  max_permission = get_module_permission(request.user, 'materials')

  if max_permission == 0:
    return redirect('dashboard')

  materials_list = Material.objects.all()

  id_material = request.GET.get('id_material')
  name = request.GET.get('name')
  material_type = request.GET.get('material_type')
  status = request.GET.get('status')

  if id_material:
    materials_list = materials_list.filter(id_material__icontains=id_material)
  if name:
    materials_list = materials_list.filter(name__icontains=name)
  if material_type:
    materials_list = materials_list.filter(material_type=material_type)
  if status is not None and status != '':
    materials_list = materials_list.filter(status=status)

  if request.GET.get('export') == "csv":
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="materials.csv"'

    response.write('\ufeff'.encode('utf-8'))
    writer = csv.writer(response)

    writer.writerow(["ID Material", 'Nombre', 'Descripción', 'Unidad', 'Tipo', 'Status', 'Creado Por', 'Creado En', 'Actualizado En'])

    for material in materials_list:
      writer.writerow([
        material.id_material,
        material.name,
        material.description,
        material.unit,
        material.material_type,
        material.status,
        material.created_by.username if material.created_by else 'N/A',
        material.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        material.updated_at.strftime('%Y-%m-%d %H:%M:%S')
      ])
    return response

  
  paginator = Paginator(materials_list, 10)
  page_number = request.GET.get('page')
  page_obj = paginator.get_page(page_number)

  all_materials = Material.objects.all()

  context = {
    'page_obj': page_obj,
    'all_material_types': get_material_types(),
    'has_filters': any([id_material, name, material_type, status]),
    'summary': {
      'total': all_materials.count(),
      'active': all_materials.filter(status='Active').count(),
      'inactive': all_materials.filter(status='Inactive').count(),
      'types': get_material_types().count(),
    },
  }

  return render(request, 'materials/materials_list.html', context)

@login_required
def material_create(request):
  max_permission = get_module_permission(request.user, 'materials')

  if max_permission == 1:
    return redirect('materials:materials_list')
  if max_permission == 0:
    return redirect('dashboard')
  
  if request.method == 'POST':
    form = MaterialForm(request.POST)
    if form.is_valid():
      material = form.save(commit=False)
      material.created_by = request.user
      material.save()

      messages.success(request, 'El material se creó correctamente.')
      return redirect('materials:materials_list')
  else:
    form = MaterialForm(initial={'status': 'Active'})

  context = {
    'form': form,
    'material_types': get_material_types(),
  }

  return render(request, 'materials/material_form.html', context)

@login_required
def material_edit(request,pk):
  max_permission = get_module_permission(request.user, 'materials')

  if max_permission == 1:
    return redirect('materials:materials_list')
  if max_permission == 0:
    return redirect('dashboard')

  material = get_object_or_404(Material, pk=pk)

  if request.method == 'POST':
    form = MaterialForm(request.POST, instance=material)
    if form.is_valid():
      form.save()
      messages.success(request, 'Los cambios del material se guardaron correctamente.')
      return redirect('materials:materials_list')
  else:
    form = MaterialForm(instance=material)
    
  context = {
    'form': form,
    'material': material,
    'material_types': get_material_types(),
  }

  return render(request, 'materials/material_form.html', context)

@login_required
def material_delete(request, pk):
  max_permission = get_module_permission(request.user, 'materials')

  if max_permission < 2:
    return redirect('materials:materials_list')

  material = get_object_or_404(Material, pk=pk)

  if request.method == 'POST':
    material.delete()
    messages.success(request, 'El material se eliminó correctamente.')
    return redirect('materials:materials_list')

  return redirect('materials:materials_list')

@login_required
def material_bulk_create(request):
  max_permission = get_module_permission(request.user, 'materials')

  if max_permission < 2:
    return redirect('materials:materials_list')

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
          return render(request, 'materials/material_bulk_upload.html', {'form': form, 'error_message': f'Error al leer el archivo CSV: {str(e)}'})

      io_string = io.StringIO(data_set)
      reader = csv.DictReader(io_string)

      if reader.fieldnames:
        if reader.fieldnames[0].startswith('\ufeff'):
          reader.fieldnames[0] = reader.fieldnames[0].lstrip('\ufeff')

        cleaned_fieldnames = [key.strip().lower() for key in reader.fieldnames]
        reader.fieldnames = cleaned_fieldnames

      successful_records = []
      error_records = []
      materials_to_create = []
      # Fila donde apareció cada id_material: la validación del formulario solo compara contra la base de datos
      seen_ids = {}

      for i, row in enumerate(reader):
        row_number = i + 2
        form_data = {}

        for key, value in row.items():
          cleaned_value = value.strip() if isinstance(value, str) else value
          form_data[key] = cleaned_value

        material_form = MaterialForm(form_data)

        if material_form.is_valid():
          id_material = material_form.cleaned_data['id_material']
          if id_material in seen_ids:
            error_records.append({
              'row': row_number,
              'data': form_data,
              'errors': {'id_material': f'Está repetido en el archivo (ya aparece en la fila {seen_ids[id_material]}).'},
            })
            continue

          seen_ids[id_material] = row_number
          material = material_form.save(commit=False)
          material.created_by = request.user
          materials_to_create.append(material)
          successful_records.append({'row': row_number, 'data': form_data})
        else:
          errors = {
            field: ', '.join(err)
            for field, err in material_form.errors.items()
          }
          error_records.append({'row': row_number, 'data': form_data, 'errors': errors})

      if materials_to_create:
        try:
          with transaction.atomic():
            Material.objects.bulk_create(materials_to_create)
        except IntegrityError:
          # Otro usuario registró alguno de estos ID mientras se procesaba el archivo
          return render(request, 'materials/material_bulk_upload.html', {
            'form': form,
            'error_message': 'Algunos ID de material ya existen. No se registró ningún material; vuelve a subir el archivo.',
          })

      if successful_records:
        count = len(successful_records)
        messages.success(request, 'Se registró 1 material.' if count == 1 else f'Se registraron {count} materiales.')
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

      return render(request, 'materials/material_bulk_upload.html', context)

    return render(request, 'materials/material_bulk_upload.html', {'form': form, 'material_types': get_material_types()})

  form = CsvUploadForm()
  return render(request, 'materials/material_bulk_upload.html', {'form': form, 'material_types': get_material_types()})

@login_required
def download_template_materials(request):
  max_permission = get_module_permission(request.user, 'materials')

  if max_permission < 2:
    return redirect('materials:materials_list')

  response = HttpResponse(content_type='text/csv')
  response['Content-Disposition'] = 'attachment; filename="material_template.csv"'

  writer = csv.writer(response)
  writer.writerow(['id_material', 'name', 'description', 'unit', 'material_type', 'status'])

  return response
