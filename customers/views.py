import csv

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.core.paginator import Paginator

from core.bulk import catalog_lookup, process_bulk_upload, status_lookup
from core.models import Country, Status, Currency
from users.permissions import get_module_permission
from .models import Customer
from .forms import CustomerForm, CsvUploadForm

TEMPLATE_HEADERS = ['id_customer', 'name', 'tax_id', 'country', 'state', 'city', 'address', 'zip_code', 'phone', 'email', 'payment_terms', 'currency', 'payment_method', 'bank_account', 'status']

def get_customer_countries():
  """Países del catálogo que tienen al menos un cliente (para el resumen)."""
  return Country.objects.filter(customer__isnull=False).distinct().order_by('name')

def get_catalogs():
  """Catálogos que usan el formulario y la carga masiva."""
  return {
    'all_countries': Country.objects.order_by('name'),
    'all_currencies': Currency.objects.order_by('code'),
    'all_status': Status.objects.order_by('name'),
  }

@login_required
def customers_list(request):
  max_permission = get_module_permission(request.user, 'customers')

  if max_permission == 0:
    return redirect('dashboard')

  customers_list = Customer.objects.select_related('created_by', 'status', 'country', 'currency')

  id_customer = request.GET.get('id_customer')
  name = request.GET.get('name')
  country = request.GET.get('country')
  status = request.GET.get('status')

  if id_customer:
    customers_list = customers_list.filter(id_customer__icontains=id_customer)
  if name:
    customers_list = customers_list.filter(name__icontains=name)
  if country:
    customers_list = customers_list.filter(country__abbreviation__iexact=country)
  if status is not None and status != '':
    customers_list = customers_list.filter(status__name__iexact=status)

  if request.GET.get('export') == "csv":
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="customers.csv"'

    response.write('﻿'.encode('utf-8'))
    writer = csv.writer(response)

    writer.writerow(['ID Cliente', 'Nombre', 'ID Fiscal', 'País', 'Estado/Provincia', 'Ciudad', 'Dirección', 'Código Postal', 'Teléfono', 'Email', 'Términos de Pago', 'Moneda', 'Método de Pago', 'Cuenta Bancaria', 'Status', 'Creado Por', 'Creado En', 'Actualizado En'])

    for customer in customers_list:
      writer.writerow([
        customer.id_customer,
        customer.name,
        customer.tax_id,
        customer.country.abbreviation if customer.country else '',
        customer.state,
        customer.city,
        customer.address,
        customer.zip_code,
        customer.phone,
        customer.email,
        customer.payment_terms,
        customer.currency.code if customer.currency else '',
        customer.payment_method,
        customer.bank_account,
        customer.status.name if customer.status else '',
        f"{customer.created_by.first_name} {customer.created_by.last_name}" if customer.created_by else '',
        customer.created_at.strftime('%Y-%m-%d %H:%M:%S') if customer.created_at else '',
        customer.updated_at.strftime('%Y-%m-%d %H:%M:%S') if customer.updated_at else '',
      ])
    return response

  paginator = Paginator(customers_list, 10)
  page_number = request.GET.get('page')
  page_obj = paginator.get_page(page_number)

  all_customers = Customer.objects.all()

  context = {
    'page_obj': page_obj,
    'all_countries': Country.objects.order_by('name'),
    'all_status': Status.objects.order_by('name'),
    'has_filters': any([id_customer, name, country, status]),
    'summary': {
      'total': all_customers.count(),
      'active': all_customers.filter(status__is_active=True).count(),
      'inactive': all_customers.filter(status__is_active=False).count(),
      'countries': get_customer_countries().count(),
    },
  }

  return render(request, 'customers/customers_list.html', context)

@login_required
def customer_create(request):
  max_permission = get_module_permission(request.user, 'customers')

  if max_permission == 1:
    return redirect('customers:customers_list')
  if max_permission == 0:
    return redirect('dashboard')

  if request.method == 'POST':
    form = CustomerForm(request.POST)
    if form.is_valid():
      customer = form.save(commit=False)
      customer.created_by = request.user
      customer.save()

      messages.success(request, 'El cliente se creó correctamente.')
      return redirect('customers:customers_list')
  else:
    form = CustomerForm()

  context = {'form': form, **get_catalogs()}
  return render(request, 'customers/customer_form.html', context)

@login_required
def customer_edit(request, pk):
  max_permission = get_module_permission(request.user, 'customers')

  if max_permission == 1:
    return redirect('customers:customers_list')
  if max_permission == 0:
    return redirect('dashboard')

  customer = get_object_or_404(Customer, pk=pk)

  if request.method == 'POST':
    form = CustomerForm(request.POST, instance=customer)
    if form.is_valid():
      form.save()
      messages.success(request, 'Los cambios del cliente se guardaron correctamente.')
      return redirect('customers:customers_list')
  else:
    form = CustomerForm(instance=customer)

  context = {'form': form, 'customer': customer, **get_catalogs()}
  return render(request, 'customers/customer_form.html', context)

@login_required
def customer_delete(request, pk):
  max_permission = get_module_permission(request.user, 'customers')

  if max_permission < 2:
    return redirect('customers:customers_list')

  customer = get_object_or_404(Customer, pk=pk)

  if request.method == 'POST':
    customer.delete()
    messages.success(request, 'El cliente se eliminó correctamente.')

  return redirect('customers:customers_list')

@login_required
def customer_bulk_create(request):
  max_permission = get_module_permission(request.user, 'customers')

  if max_permission < 2:
    return redirect('customers:customers_list')

  context = {}

  if request.method == 'POST':
    form = CsvUploadForm(request.POST, request.FILES)
    if form.is_valid():
      context = process_bulk_upload(
        request,
        form.cleaned_data['csv_file'],
        form_class=CustomerForm,
        model=Customer,
        id_field='id_customer',
        # País y moneda se aceptan por nombre, abreviación/código o ambos ("México", "MX" o "México (MX)")
        catalogs={
          'country': catalog_lookup(Country.objects.all(), 'name', 'abbreviation', str),
          'currency': catalog_lookup(Currency.objects.all(), 'code', 'name', str),
          'status': status_lookup(),
        },
        nouns=('cliente', 'clientes'),
      )
  else:
    form = CsvUploadForm()

  context.update({'form': form, **get_catalogs()})
  return render(request, 'customers/customer_bulk_upload.html', context)

@login_required
def download_template_customers(request):
  max_permission = get_module_permission(request.user, 'customers')

  if max_permission < 2:
    return redirect('customers:customers_list')

  response = HttpResponse(content_type='text/csv')
  response['Content-Disposition'] = 'attachment; filename="customer_template.csv"'

  writer = csv.writer(response)
  writer.writerow(TEMPLATE_HEADERS)

  return response
