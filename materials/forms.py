from django import forms
from core.models import Status
from .models import Material

class MaterialForm(forms.ModelForm):

  class Meta:
    model = Material
    fields = ['id_material', 'name', 'description', 'unit', 'material_type', 'status']

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    if not self.instance.pk and not self.is_bound:
      # El modelo usa default=1 en los catálogos; en un material nuevo el usuario debe elegir
      # unidad y tipo, y el estado empieza en el primer estado activo (sea cual sea su id)
      self.initial['unit'] = None
      self.initial['material_type'] = None
      self.initial['status'] = Status.default_pk()

class CsvUploadForm(forms.Form):
    csv_file = forms.FileField(
       label='Seleccionar archivo CSV',
       required=True,
       help_text='Seleccione un archivo CSV para cargar los materiales.')