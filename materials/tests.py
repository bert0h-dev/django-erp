import csv
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from core.models import Status
from users.models import Role, User, UserRole
from .models import Material, MaterialType, Unit


class MaterialTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ana', password='Clave-segura-123')
        self.client.force_login(self.user)
        self.kg = Unit.objects.create(name='Kilogramos', symbol='kg')
        self.metal = MaterialType.objects.create(name='Metal')
        # Los crea la migración core.0002_default_statuses
        self.active = Status.objects.get(name='Activo')
        self.inactive = Status.objects.get(name='Inactivo')

    def material_type(self, name):
        return MaterialType.objects.get_or_create(name=name)[0]

    def set_level(self, level):
        role = Role.objects.create(role_name=f'Materiales {level}', materials=level)
        UserRole.objects.create(user_id=self.user, role=role)

    def create_material(self, code, **fields):
        data = {
            'id_material': code,
            'name': f'Material {code}',
            'unit': self.kg,
            'material_type': self.metal,
            'status': self.active,
        }
        data.update(fields)
        if isinstance(data['material_type'], str):
            data['material_type'] = self.material_type(data['material_type'])
        return Material.objects.create(**data)


class MaterialPermissionTests(MaterialTestCase):
    def setUp(self):
        super().setUp()
        self.material = self.create_material('M-1')
        self.list_url = reverse('materials:materials_list')
        self.edit_url = reverse('materials:material_edit', args=[self.material.pk])
        self.delete_url = reverse('materials:material_delete', args=[self.material.pk])

    def test_no_access_redirects_to_dashboard(self):
        for url in (self.list_url, reverse('materials:material_create'), self.edit_url):
            with self.subTest(url=url):
                self.assertRedirects(self.client.get(url), reverse('dashboard'))

    def test_no_access_to_missing_material_does_not_reveal_it(self):
        response = self.client.get(reverse('materials:material_edit', args=[9999]))
        self.assertRedirects(response, reverse('dashboard'))

    def test_read_only_can_list_but_not_write(self):
        self.set_level(1)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse('materials:material_create'))

        self.assertRedirects(self.client.get(reverse('materials:material_create')), self.list_url)
        self.assertRedirects(self.client.get(self.edit_url), self.list_url)
        self.assertRedirects(self.client.post(self.delete_url), self.list_url)
        self.assertTrue(Material.objects.filter(pk=self.material.pk).exists())

    def test_read_write_sees_actions(self):
        self.set_level(2)
        response = self.client.get(self.list_url)
        self.assertContains(response, reverse('materials:material_create'))
        self.assertContains(response, self.edit_url)


class MaterialCrudTests(MaterialTestCase):
    def setUp(self):
        super().setUp()
        self.set_level(2)

    def test_create_assigns_creator(self):
        response = self.client.post(reverse('materials:material_create'), {
            'id_material': 'M-100',
            'name': 'Acero',
            'description': '',
            'unit': self.kg.pk,
            'material_type': self.metal.pk,
            'status': self.active.pk,
        })

        self.assertRedirects(response, reverse('materials:materials_list'))
        material = Material.objects.get(id_material='M-100')
        self.assertEqual(material.created_by, self.user)
        self.assertEqual((material.unit, material.material_type, material.status), (self.kg, self.metal, self.active))

    def test_create_form_starts_without_unit_and_type(self):
        form = self.client.get(reverse('materials:material_create')).context['form']

        self.assertIsNone(form.initial['unit'])
        self.assertIsNone(form.initial['material_type'])
        self.assertEqual(form.initial['status'], self.active.pk)

    def test_edit_updates_material(self):
        material = self.create_material('M-1')

        response = self.client.post(reverse('materials:material_edit', args=[material.pk]), {
            'id_material': 'M-1',
            'name': 'Nombre nuevo',
            'description': '',
            'unit': self.kg.pk,
            'material_type': self.metal.pk,
            'status': self.inactive.pk,
        })

        self.assertRedirects(response, reverse('materials:materials_list'))
        material.refresh_from_db()
        self.assertEqual(material.name, 'Nombre nuevo')
        self.assertEqual(material.status, self.inactive)

    def test_delete_requires_post(self):
        material = self.create_material('M-1')
        url = reverse('materials:material_delete', args=[material.pk])

        self.client.get(url)
        self.assertTrue(Material.objects.filter(pk=material.pk).exists())

        self.client.post(url)
        self.assertFalse(Material.objects.filter(pk=material.pk).exists())


class MaterialListTests(MaterialTestCase):
    def setUp(self):
        super().setUp()
        self.set_level(1)
        self.url = reverse('materials:materials_list')

    def test_material_type_filter_options_and_exact_match(self):
        self.create_material('M-1', material_type='A & B')
        self.create_material('M-2', material_type='A & B extra')
        self.create_material('M-3', material_type='Metal')

        response = self.client.get(self.url, {'material_type': 'A & B'})

        self.assertEqual([t.name for t in response.context['all_material_types']], ['A & B', 'A & B extra', 'Metal'])
        self.assertEqual([m.id_material for m in response.context['page_obj']], ['M-1'])
        self.assertContains(response, '<option value="A &amp; B" selected>')

    def test_status_filter_and_summary_use_catalog(self):
        self.create_material('M-1')
        self.create_material('M-2', status=self.inactive)

        response = self.client.get(self.url, {'status': 'Inactivo'})

        self.assertEqual([m.id_material for m in response.context['page_obj']], ['M-2'])
        self.assertEqual(response.context['summary']['active'], 1)
        self.assertEqual(response.context['summary']['inactive'], 1)
        self.assertContains(response, '<span class="portal-status portal-status--inactive">Inactivo</span>')

    def test_pagination_is_ordered_and_keeps_encoded_filters(self):
        for i in range(25):
            self.create_material(f'M-{i:02}', material_type='A & B')

        first = self.client.get(self.url, {'material_type': 'A & B'})
        second = self.client.get(self.url, {'material_type': 'A & B', 'page': 2})

        self.assertContains(first, '?material_type=A+%26+B&amp;page=2')
        self.assertContains(first, '?material_type=A+%26+B&amp;export=csv')
        first_ids = {m.pk for m in first.context['page_obj']}
        second_ids = {m.pk for m in second.context['page_obj']}
        self.assertEqual(len(first_ids), 10)
        self.assertFalse(first_ids & second_ids)
        # Orden por defecto: más recientes primero.
        self.assertEqual(first.context['page_obj'][0].id_material, 'M-24')

    def test_csv_export_respects_filters(self):
        self.create_material('M-1', material_type='Metal')
        self.create_material('M-2', material_type='Madera')

        response = self.client.get(self.url, {'material_type': 'Metal', 'export': 'csv'})

        self.assertEqual(response['Content-Type'], 'text/csv')
        rows = list(csv.reader(io.StringIO(response.content.decode('utf-8-sig'))))
        self.assertEqual(rows[0][0], 'ID Material')
        self.assertEqual([row[0] for row in rows[1:]], ['M-1'])


class MaterialModelTests(TestCase):
    def test_str_falls_back_when_name_is_empty(self):
        self.assertEqual(str(Material(name='Acero')), 'Acero')
        self.assertEqual(str(Material(name='', id_material='M-1')), 'M-1')
        self.assertEqual(str(Material(name='', pk=7)), 'Material 7')


class MaterialBulkUploadTests(MaterialTestCase):
    HEADERS = ['id_material', 'name', 'description', 'unit', 'material_type', 'status']

    def setUp(self):
        super().setUp()
        self.set_level(2)
        self.url = reverse('materials:material_bulk_create')

    def row(self, code, **fields):
        data = {'id_material': code, 'name': f'Material {code}', 'description': '', 'unit': 'kg', 'material_type': 'Metal', 'status': 'Activo'}
        data.update(fields)
        return data

    def csv_file(self, rows):
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.HEADERS)
        writer.writeheader()
        writer.writerows(rows)
        return SimpleUploadedFile('materiales.csv', output.getvalue().encode('utf-8'), content_type='text/csv')

    def test_read_only_is_redirected(self):
        Role.objects.filter(role_name='Materiales 2').update(materials=1)
        list_url = reverse('materials:materials_list')
        self.assertRedirects(self.client.get(self.url), list_url)
        self.assertRedirects(self.client.get(reverse('materials:download_template_materials')), list_url)

    def test_upload_page_renders(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="csv_file"')
        self.assertContains(response, reverse('materials:download_template_materials'))

    def test_template_has_expected_headers(self):
        response = self.client.get(reverse('materials:download_template_materials'))
        self.assertEqual(response.content.decode().strip(), ','.join(self.HEADERS))

    def test_upload_reports_created_and_failed_rows(self):
        rows = [self.row('M-10'), self.row('M-11', unit='')]

        response = self.client.post(self.url, {'csv_file': self.csv_file(rows)})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Material.objects.get(id_material='M-10').created_by, self.user)
        self.assertFalse(Material.objects.filter(id_material='M-11').exists())
        self.assertContains(response, 'Filas con errores')
        self.assertContains(response, 'Materiales registrados (1)')

    def test_duplicate_id_in_file_is_reported_not_crashing(self):
        rows = [self.row('M-20'), self.row('M-20', name='Otro')]

        response = self.client.post(self.url, {'csv_file': self.csv_file(rows)})

        self.assertEqual(Material.objects.filter(id_material='M-20').count(), 1)
        self.assertContains(response, 'ya aparece en la fila 2')

    def test_messages_reflect_result(self):
        response = self.client.post(self.url, {'csv_file': self.csv_file([self.row('M-30'), self.row('M-31')])})

        texts = [str(message) for message in response.context['messages']]
        self.assertEqual(texts, ['Se registraron 2 materiales.'])

    def test_upload_without_file_shows_error(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'aria-invalid="true"')

    def test_unknown_catalog_values_are_rejected(self):
        rows = [self.row('M-40', status='Pendiente', unit='toneladas', material_type='Madera')]

        response = self.client.post(self.url, {'csv_file': self.csv_file(rows)})

        self.assertFalse(Material.objects.filter(id_material='M-40').exists())
        errors = response.context['error_records'][0]['errors']
        self.assertEqual(errors['status'], '«Pendiente» no existe en el catálogo.')
        self.assertEqual(errors['unit'], '«toneladas» no existe en el catálogo.')
        self.assertEqual(errors['material_type'], '«Madera» no existe en el catálogo.')

    def test_catalog_text_is_resolved_by_name_or_symbol(self):
        rows = [
            self.row('M-50', unit='KILOGRAMOS', material_type='metal', status='inactivo'),
            self.row('M-51', unit='kg', status='Active'),
            self.row('M-52', unit='Kilogramos (kg)'),  # como la pone la exportación
        ]

        response = self.client.post(self.url, {'csv_file': self.csv_file(rows)})

        first = Material.objects.get(id_material='M-50')
        self.assertEqual((first.unit, first.material_type, first.status), (self.kg, self.metal, self.inactive))
        self.assertEqual(Material.objects.get(id_material='M-51').status, self.active)
        self.assertEqual(Material.objects.get(id_material='M-52').unit, self.kg)
        # El reporte muestra el registro del catálogo, no el texto del CSV
        self.assertContains(response, 'Kilogramos (kg)')

    def test_excel_csv_with_bom_and_latin1_is_read(self):
        content = '\ufeffid_material,name,description,unit,material_type,status\r\nM-60,Ñandú,,kg,Metal,Activo\r\n'
        for encoding in ('utf-8', 'iso-8859-1'):
            with self.subTest(encoding=encoding):
                Material.objects.filter(id_material='M-60').delete()
                data = content.encode(encoding) if encoding == 'utf-8' else content.lstrip('\ufeff').encode(encoding)
                upload = SimpleUploadedFile('materiales.csv', data, content_type='text/csv')

                self.client.post(self.url, {'csv_file': upload})

                self.assertEqual(Material.objects.get(id_material='M-60').name, 'Ñandú')
