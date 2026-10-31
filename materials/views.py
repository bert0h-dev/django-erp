from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Material
from .forms import MaterialForm
from django.core.paginator import Paginator
from django.http import HttpResponse
import csv
from users.permissions import get_module_permission

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

    writer.writerow(["ID Material", 'Name', 'Description', 'Unit', 'Type', 'Status', 'Created By', 'Created At', 'Update At'])

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

  all_material_types = (
    Material.objects.exclude(material_type='')
    .order_by('material_type')
    .values_list('material_type', flat=True)
    .distinct()
  )

  context = {
    'page_obj': page_obj,
    'all_material_types': all_material_types,
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

  return render(request, 'materials/material_form.html', {'form': form})

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