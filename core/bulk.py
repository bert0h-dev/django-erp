"""Carga masiva desde CSV, compartida por los módulos (materiales, proveedores).

Cada fila se valida con el ModelForm del módulo. Los campos de catálogo (ForeignKey) llegan en el
CSV como texto, por ejemplo "kg" o "Activo", y se traducen al id del registro antes de validar.
"""
import csv
import io

from django.contrib import messages
from django.db import IntegrityError, transaction

from .models import Status


def catalog_lookup(queryset, *fields):
    """Índice {texto en minúsculas: registro} con el valor de cada uno de `fields`.

    Un campo puede ser el nombre de un atributo o una función; con `str` también se acepta el texto
    que pone la exportación a CSV (p. ej. "México (MX)"), para copiar valores de una exportación.
    """
    lookup = {}
    for item in queryset:
        for field in fields:
            value = field(item) if callable(field) else getattr(item, field)
            if value:
                lookup.setdefault(str(value).strip().lower(), item)
    return lookup


def status_lookup():
    """Estados por nombre; también acepta Active/Inactive (como decía la plantilla anterior)."""
    statuses = list(Status.objects.order_by('pk'))
    lookup = catalog_lookup(statuses, 'name')
    for alias, is_active in (('active', True), ('inactive', False)):
        match = next((status for status in statuses if status.is_active == is_active), None)
        if match:
            lookup.setdefault(alias, match)
    return lookup


def read_csv_rows(csv_file):
    """Filas del CSV como dicts, con los encabezados en minúsculas y sin espacios."""
    raw = csv_file.read()
    try:
        text = raw.decode('utf-8-sig')  # también quita el BOM que agrega Excel
    except UnicodeDecodeError:
        text = raw.decode('iso-8859-1')

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames:
        reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]

    for row in reader:
        yield {
            key: value.strip() if isinstance(value, str) else ''
            for key, value in row.items()
            if key
        }


def process_bulk_upload(request, csv_file, *, form_class, model, id_field, catalogs, nouns):
    """Registra las filas válidas del CSV y devuelve el contexto del reporte.

    `catalogs` es {campo: lookup} para los ForeignKey; `nouns` es (singular, plural) para los mensajes.
    Si el archivo no se puede procesar, devuelve {'error_message': ...}.
    """
    singular, plural = nouns
    successful_records = []
    error_records = []
    objects_to_create = []
    # Fila donde apareció cada ID: la validación del formulario solo compara contra la base de datos
    seen_ids = {}

    try:
        rows = list(read_csv_rows(csv_file))
    except csv.Error as error:
        return {'error_message': f'No se pudo leer el archivo CSV: {error}'}

    for index, data in enumerate(rows):
        row_number = index + 2  # la fila 1 son los encabezados
        form_data = dict(data)
        errors = {}
        catalog_values = {}

        for field, lookup in catalogs.items():
            value = data.get(field, '')
            if not value:
                continue  # el formulario lo marca como obligatorio
            item = lookup.get(value.lower())
            if item is None:
                errors[field] = f'«{value}» no existe en el catálogo.'
            else:
                form_data[field] = item.pk
                catalog_values[field] = item

        form = form_class(form_data)
        if not form.is_valid():
            for field, field_errors in form.errors.items():
                errors.setdefault(field, ', '.join(field_errors))
        elif form.cleaned_data[id_field] in seen_ids:
            errors[id_field] = f'Está repetido en el archivo (ya aparece en la fila {seen_ids[form.cleaned_data[id_field]]}).'

        if errors:
            error_records.append({'row': row_number, 'data': data, 'errors': errors})
            continue

        seen_ids[form.cleaned_data[id_field]] = row_number
        instance = form.save(commit=False)
        instance.created_by = request.user
        objects_to_create.append(instance)
        successful_records.append({'row': row_number, 'data': data, 'catalog': catalog_values})

    if objects_to_create:
        try:
            with transaction.atomic():
                model.objects.bulk_create(objects_to_create)
        except IntegrityError:
            # Otro usuario registró alguno de estos ID mientras se procesaba el archivo
            return {'error_message': f'Algunos ID ya existen. No se registró ningún {singular}; vuelve a subir el archivo.'}

    if successful_records:
        count = len(successful_records)
        messages.success(request, f'Se registró 1 {singular}.' if count == 1 else f'Se registraron {count} {plural}.')
    if error_records:
        count = len(error_records)
        messages.warning(request, '1 fila tiene errores y no se registró.' if count == 1 else f'{count} filas tienen errores y no se registraron.')

    return {
        'report_generated': True,
        'successful_count': len(successful_records),
        'error_count': len(error_records),
        'total_rows': len(rows),
        'successful_records': successful_records,
        'error_records': error_records,
    }
