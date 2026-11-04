from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from core.bulk import catalog_lookup, process_bulk_upload, status_lookup
from core.models import Status
from .models import Material, MaterialType, Unit
from .forms import MaterialForm, CsvUploadForm
from django.core.paginator import Paginator
from django.http import HttpResponse
import csv
from users.permissions import get_module_permission

def get_catalogs():
  """Opciones de los catálogos que usan los formularios, filtros e instrucciones de materiales."""
  return {
    'all_units': Unit.objects.order_by('name'),
    'all_material_types': MaterialType.objects.order_by('name'),
    'all_status': Status.objects.order_by('name'),
  }

@login_required
def materials_list(request):
  max_permission = get_module_permission(request.user, 'materials')

  if max_permission == 0:
    return redirect('dashboard')

  materials_list = Material.objects.select_related('created_by', 'unit', 'material_type', 'status')

  id_material = request.GET.get('id_material')
  name = request.GET.get('name')
  material_type = request.GET.get('material_type')
  status = request.GET.get('status')

  if id_material:
    materials_list = materials_list.filter(id_material__icontains=id_material)
  if name:
    materials_list = materials_list.filter(name__icontains=name)
  if material_type:
    try:
      material_type_obj = MaterialType.objects.get(name__iexact=material_type)
      materials_list = materials_list.filter(material_type=material_type_obj)
    except MaterialType.DoesNotExist:
      materials_list = materials_list.none()
  if status:
    try:
      status_obj = Status.objects.get(name__iexact=status)
      materials_list = materials_list.filter(status=status_obj)
    except Status.DoesNotExist:
      materials_list = materials_list.none()

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

  # Se obtiene el total de materiales para el resumen
  all_materials = Material.objects.all()

  context = {
    'page_obj': page_obj,
    **get_catalogs(),
    'has_filters': any([id_material, name, material_type, status]),
    'summary': {
      'total': all_materials.count(),
      'active': all_materials.filter(status__is_active=True).count(),
      'inactive': all_materials.filter(status__is_active=False).count(),
      'types': MaterialType.objects.count(),
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
    form = MaterialForm()

  context = {
    'form': form,
    **get_catalogs(),
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
    **get_catalogs(),
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

  context = {}

  if request.method == 'POST':
    form = CsvUploadForm(request.POST, request.FILES)
    if form.is_valid():
      context = process_bulk_upload(
        request,
        form.cleaned_data['csv_file'],
        form_class=MaterialForm,
        model=Material,
        id_field='id_material',
        # La unidad se puede escribir por nombre, símbolo o como la exporta el listado ("Kilogramos", "kg" o "Kilogramos (kg)")
        catalogs={
          'unit': catalog_lookup(Unit.objects.all(), 'name', 'symbol', str),
          'material_type': catalog_lookup(MaterialType.objects.all(), 'name'),
          'status': status_lookup(),
        },
        nouns=('material', 'materiales'),
      )
  else:
    form = CsvUploadForm()

  context.update({'form': form, **get_catalogs()})
  return render(request, 'materials/material_bulk_upload.html', context)

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
