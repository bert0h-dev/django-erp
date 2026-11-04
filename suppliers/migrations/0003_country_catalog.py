import django.db.models.deletion
from django.db import migrations, models


def link_countries(apps, schema_editor):
    """Traduce el país que estaba como texto al registro del catálogo (por nombre o abreviación)."""
    Suppliers = apps.get_model('suppliers', 'Suppliers')
    Country = apps.get_model('core', 'Country')
    countries = {}
    for country in Country.objects.all():
        countries[country.name.strip().lower()] = country
        countries[country.abbreviation.strip().lower()] = country

    missing = set()
    for supplier in Suppliers.objects.all():
        country = countries.get((supplier.country or '').strip().lower())
        if country is None:
            missing.add(supplier.country)
            continue
        supplier.country_ref = country
        supplier.save(update_fields=['country_ref'])

    if missing:
        raise RuntimeError(
            'Estos países de proveedores no existen en el catálogo core.Country: '
            f'{", ".join(sorted(repr(name) for name in missing))}. Agrégalos o corrige el proveedor y vuelve a migrar.'
        )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_default_countries_currencies'),
        ('suppliers', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='suppliers',
            name='country_ref',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='core.country'),
        ),
        migrations.RunPython(link_countries, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='suppliers',
            name='country',
        ),
        migrations.RenameField(
            model_name='suppliers',
            old_name='country_ref',
            new_name='country',
        ),
        migrations.AlterField(
            model_name='suppliers',
            name='country',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.country', verbose_name='Country'),
        ),
    ]
