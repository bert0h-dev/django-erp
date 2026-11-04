from django.db import migrations

# Materiales y proveedores usan default=1 en `status`: estos dos estados deben existir en toda base de datos
DEFAULT_STATUSES = [('Activo', True), ('Inactivo', False)]


def create_default_statuses(apps, schema_editor):
    Status = apps.get_model('core', 'Status')
    for name, is_active in DEFAULT_STATUSES:
        Status.objects.get_or_create(name=name, defaults={'is_active': is_active})


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_statuses, migrations.RunPython.noop),
    ]
