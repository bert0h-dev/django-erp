import csv
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from users.models import Role, User, UserRole
from .models import Material


class MaterialTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ana', password='Clave-segura-123')
        self.client.force_login(self.user)

    def set_level(self, level):
        role = Role.objects.create(role_name=f'Materiales {level}', materials=level)
        UserRole.objects.create(user_id=self.user, role=role)

    def create_material(self, code, **fields):
        data = {
            'id_material': code,
            'name': f'Material {code}',
            'unit': 'kg',
            'material_type': 'Metal',
            'status': 'Active',
        }
        data.update(fields)
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
            'unit': 'kg',
            'material_type': 'Metal',
            'status': 'Active',
        })

        self.assertRedirects(response, reverse('materials:materials_list'))
        material = Material.objects.get(id_material='M-100')
        self.assertEqual(material.created_by, self.user)

    def test_edit_updates_material(self):
        material = self.create_material('M-1')

        response = self.client.post(reverse('materials:material_edit', args=[material.pk]), {
            'id_material': 'M-1',
            'name': 'Nombre nuevo',
            'description': '',
            'unit': 'kg',
            'material_type': 'Metal',
            'status': 'Inactive',
        })

        self.assertRedirects(response, reverse('materials:materials_list'))
        material.refresh_from_db()
        self.assertEqual(material.name, 'Nombre nuevo')
        self.assertEqual(material.status, 'Inactive')

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

        self.assertEqual(list(response.context['all_material_types']), ['A & B', 'A & B extra', 'Metal'])
        self.assertEqual([m.id_material for m in response.context['page_obj']], ['M-1'])

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
        data = {'id_material': code, 'name': f'Material {code}', 'description': '', 'unit': 'kg', 'material_type': 'Metal', 'status': 'Active'}
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

    def test_unknown_status_is_rejected(self):
        response = self.client.post(self.url, {'csv_file': self.csv_file([self.row('M-40', status='Pendiente')])})

        self.assertFalse(Material.objects.filter(id_material='M-40').exists())
        self.assertContains(response, 'no es un estado válido')
