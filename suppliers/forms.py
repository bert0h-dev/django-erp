from django import forms
from .models import Suppliers

class SupplierForm(forms.ModelForm):
  # El modelo guarda texto libre; aquí se limita a los dos estados que maneja el sistema
  status = forms.ChoiceField(
    choices=[('Active', 'Activo'), ('Inactive', 'Inactivo')],
    error_messages={'invalid_choice': '«%(value)s» no es un estado válido: usa Active o Inactive.'},
  )

  class Meta:
    model = Suppliers
    fields = ['id_supplier', 'legal_name', 'name', 'tax_id', 'country', 'state_province', 'city', 'address', 'zip_code', 'phone', 'email', 'contact_name', 'contact_role', 'category', 'payment_terms', 'currency', 'payment_method', 'bank_account', 'status']

class CsvUploadForm(forms.Form):
    csv_file = forms.FileField(
       label='Seleccionar archivo CSV', 
       required=True, 
       help_text='Seleccione un archivo CSV para cargar los proveedores.')