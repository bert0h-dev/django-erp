from django import forms
from core.models import Status
from .models import Customer

class CustomerForm(forms.ModelForm):
  class Meta:
    model = Customer
    fields = ['id_customer', 'name', 'tax_id', 'country', 'state', 'city', 'address', 'zip_code', 'phone', 'email', 'payment_terms', 'currency', 'payment_method', 'bank_account', 'status']

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    if not self.instance.pk and not self.is_bound:
      self.initial['status'] = Status.default_pk()

class CsvUploadForm(forms.Form):
  csv_file = forms.FileField(
    label='Seleccionar archivo CSV', 
    required=True, 
    help_text='Seleccione un archivo CSV para cargar los clientes.')