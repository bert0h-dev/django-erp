from django import forms
from .models import Material

class MaterialForm(forms.ModelForm):
  # El modelo guarda texto libre; aquí se limita a los dos estados que maneja el sistema
  status = forms.ChoiceField(
    choices=[('Active', 'Activo'), ('Inactive', 'Inactivo')],
    error_messages={'invalid_choice': '«%(value)s» no es un estado válido: usa Active o Inactive.'},
  )

  class Meta:
    model = Material
    fields = ['id_material', 'name', 'description', 'unit', 'material_type', 'status']

class CsvUploadForm(forms.Form):
    csv_file = forms.FileField(
       label='Seleccionar archivo CSV',
       required=True,
       help_text='Seleccione un archivo CSV para cargar los materiales.')