from django import forms
from core.models import Status
from .models import Suppliers

class SupplierForm(forms.ModelForm):

  class Meta:
    model = Suppliers
    fields = ['id_supplier', 'legal_name', 'name', 'tax_id', 'country', 'state_province', 'city', 'address', 'zip_code', 'phone', 'email', 'contact_name', 'contact_role', 'category', 'payment_terms', 'currency', 'payment_method', 'bank_account', 'status']

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    if not self.instance.pk and not self.is_bound:
      # El modelo usa default=1 en `status`; un proveedor nuevo empieza en el primer estado activo
      self.initial['status'] = Status.default_pk()

class CsvUploadForm(forms.Form):
    csv_file = forms.FileField(
       label='Seleccionar archivo CSV', 
       required=True, 
       help_text='Seleccione un archivo CSV para cargar los proveedores.')