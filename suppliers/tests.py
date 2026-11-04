import csv
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from django.db.models import ProtectedError

from core.models import Country, Status
from users.models import Role, User, UserRole
from .models import Suppliers


class SupplierTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ana', password='Clave-segura-123')
        self.client.force_login(self.user)
        # Los crea la migración core.0002_default_statuses
        self.active = Status.objects.get(name='Activo')
        self.inactive = Status.objects.get(name='Inactivo')
        # Los precarga la migración core.0004_default_countries_currencies
        self.mexico = Country.objects.get(abbreviation='MX')
        self.chile = Country.objects.get(abbreviation='CL')

    def set_level(self, level):
        role = Role.objects.create(role_name=f'Proveedores {level}', suppliers=level)
        UserRole.objects.create(user_id=self.user, role=role)

    def supplier_data(self, code, **fields):
        data = {
            'id_supplier': code,
            'legal_name': f'Proveedor {code} S.A. de C.V.',
            'name': f'Proveedor {code}',
            'tax_id': 'PRO010101ABC',
            'country': 'México',
            'state_province': 'Nuevo León',
            'city': 'Monterrey',
            'address': 'Av. Siempre Viva 123',
            'zip_code': 64000,
            'phone': 8112345678,
            'email': 'ventas@proveedor.com',
            'contact_name': 'Laura Pérez',
            'contact_role': 'Ventas',
            'category': 'Harinas',
            'payment_terms': '30 días',
            'currency': 'MXN',
            'payment_method': 'Transferencia',
            'bank_account': '012345678901234567',
            'status': 'Activo',  # como se escriben en el CSV
        }
        data.update(fields)
        return data

    def post_data(self, code, **fields):
        """Datos para el formulario: país y estado van como id del catálogo."""
        return {**self.supplier_data(code), 'country': self.mexico.pk, 'status': self.active.pk, **fields}

    def create_supplier(self, code, **fields):
        return Suppliers.objects.create(**{**self.supplier_data(code), 'country': self.mexico, 'status': self.active, **fields})


class SupplierPermissionTests(SupplierTestCase):
    def setUp(self):
        super().setUp()
        self.supplier = self.create_supplier('PR-1')
        self.list_url = reverse('suppliers:suppliers_list')
        self.edit_url = reverse('suppliers:supplier_edit', args=[self.supplier.pk])
        self.delete_url = reverse('suppliers:supplier_delete', args=[self.supplier.pk])

    def test_no_access_redirects_to_dashboard(self):
        for url in (self.list_url, reverse('suppliers:supplier_create'), self.edit_url):
            with self.subTest(url=url):
                self.assertRedirects(self.client.get(url), reverse('dashboard'))

    def test_read_only_can_list_but_not_write(self):
        self.set_level(1)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Proveedor PR-1')
        self.assertNotContains(response, reverse('suppliers:supplier_create'))

        self.assertRedirects(self.client.get(reverse('suppliers:supplier_create')), self.list_url)
        self.assertRedirects(self.client.get(self.edit_url), self.list_url)
        self.assertRedirects(self.client.post(self.delete_url), self.list_url)
        self.assertTrue(Suppliers.objects.filter(pk=self.supplier.pk).exists())

    def test_read_write_sees_actions(self):
        self.set_level(2)
        response = self.client.get(self.list_url)
        self.assertContains(response, reverse('suppliers:supplier_create'))
        self.assertContains(response, self.edit_url)


class SupplierCrudTests(SupplierTestCase):
    def setUp(self):
        super().setUp()
        self.set_level(2)

    def test_create_form_renders(self):
        response = self.client.get(reverse('suppliers:supplier_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nuevo proveedor')
        # Un proveedor nuevo empieza en el estado activo del catálogo
        self.assertEqual(response.context['form'].initial['status'], self.active.pk)
        self.assertContains(response, f'<option value="{self.active.pk}" data-active="true" selected>Activo</option>')

    def test_create_assigns_creator(self):
        response = self.client.post(reverse('suppliers:supplier_create'), self.post_data('PR-2'))

        self.assertRedirects(response, reverse('suppliers:suppliers_list'))
        self.assertEqual(Suppliers.objects.get(id_supplier='PR-2').created_by, self.user)

    def test_invalid_create_shows_errors(self):
        response = self.client.post(reverse('suppliers:supplier_create'), self.post_data('PR-3', email='no-es-correo'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'aria-invalid="true"')
        self.assertFalse(Suppliers.objects.filter(id_supplier='PR-3').exists())

    def test_edit_updates_supplier(self):
        supplier = self.create_supplier('PR-4')
        url = reverse('suppliers:supplier_edit', args=[supplier.pk])

        self.assertContains(self.client.get(url), 'Editar Proveedor PR-4')
        response = self.client.post(url, self.post_data('PR-4', name='Nuevo nombre', status=self.inactive.pk))

        self.assertRedirects(response, reverse('suppliers:suppliers_list'))
        supplier.refresh_from_db()
        self.assertEqual(supplier.name, 'Nuevo nombre')
        self.assertEqual(supplier.status, self.inactive)

    def test_delete_removes_supplier(self):
        supplier = self.create_supplier('PR-5')
        response = self.client.post(reverse('suppliers:supplier_delete', args=[supplier.pk]))

        self.assertRedirects(response, reverse('suppliers:suppliers_list'))
        self.assertFalse(Suppliers.objects.filter(pk=supplier.pk).exists())

    def test_country_filter_and_options(self):
        self.create_supplier('PR-6', name='Del norte', country=self.mexico)
        self.create_supplier('PR-7', name='Del sur', country=self.chile)

        response = self.client.get(reverse('suppliers:suppliers_list'), {'country': 'CL'})

        self.assertContains(response, 'Del sur')
        self.assertNotContains(response, 'Del norte')
        # El filtro ofrece todo el catálogo; el resumen cuenta solo los países con proveedores
        self.assertEqual(response.context['all_countries'].count(), Country.objects.count())
        self.assertEqual(response.context['summary']['countries'], 2)
        self.assertContains(response, '<option value="CL" selected>Chile (CL)</option>')
        self.assertContains(response, 'Nuevo León, Chile (CL)')

    def test_csv_export_shows_country_with_abbreviation(self):
        self.create_supplier('PR-72', country=self.chile)

        response = self.client.get(reverse('suppliers:suppliers_list'), {'export': 'csv'})

        rows = list(csv.reader(io.StringIO(response.content.decode('utf-8-sig'))))
        self.assertEqual(rows[1][rows[0].index('País')], 'Chile (CL)')

    def test_create_saves_country_from_catalog(self):
        response = self.client.post(reverse('suppliers:supplier_create'), self.post_data('PR-70', country=self.chile.pk))

        self.assertRedirects(response, reverse('suppliers:suppliers_list'))
        self.assertEqual(Suppliers.objects.get(id_supplier='PR-70').country, self.chile)

    def test_country_in_use_cannot_be_deleted(self):
        self.create_supplier('PR-71')
        with self.assertRaises(ProtectedError):
            self.mexico.delete()

    def test_status_filter_and_summary_use_catalog(self):
        self.create_supplier('PR-8', name='Activo uno')
        self.create_supplier('PR-9', name='Inactivo uno', status=self.inactive)

        response = self.client.get(reverse('suppliers:suppliers_list'), {'status': 'Inactivo'})

        self.assertEqual([s.id_supplier for s in response.context['page_obj']], ['PR-9'])
        self.assertEqual(response.context['summary']['active'], 1)
        self.assertEqual(response.context['summary']['inactive'], 1)
        self.assertContains(response, '<span class="portal-status portal-status--inactive">Inactivo</span>')


class SupplierBulkUploadTests(SupplierTestCase):
    def setUp(self):
        super().setUp()
        self.set_level(2)
        self.url = reverse('suppliers:supplier_bulk_create')

    def csv_file(self, rows):
        headers = list(self.supplier_data('X').keys())
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
        return SimpleUploadedFile('proveedores.csv', output.getvalue().encode('utf-8'), content_type='text/csv')

    def test_read_only_is_redirected(self):
        Role.objects.filter(role_name='Proveedores 2').update(suppliers=1)
        self.assertRedirects(self.client.get(self.url), reverse('suppliers:suppliers_list'))

    def test_upload_page_renders(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="csv_file"')
        self.assertContains(response, reverse('suppliers:download_template_suppliers'))

    def test_upload_reports_created_and_failed_rows(self):
        rows = [self.supplier_data('PR-10'), self.supplier_data('PR-11', email='no-es-correo')]

        response = self.client.post(self.url, {'csv_file': self.csv_file(rows)})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Suppliers.objects.filter(id_supplier='PR-10').exists())
        self.assertFalse(Suppliers.objects.filter(id_supplier='PR-11').exists())
        self.assertContains(response, 'Resultado de la carga')
        self.assertContains(response, 'Filas con errores')
        self.assertContains(response, 'Proveedores registrados (1)')

    def test_upload_without_file_shows_error(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'aria-invalid="true"')

    def test_duplicate_id_in_file_is_reported_not_crashing(self):
        rows = [self.supplier_data('PR-20'), self.supplier_data('PR-20', name='Otro')]

        response = self.client.post(self.url, {'csv_file': self.csv_file(rows)})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Suppliers.objects.filter(id_supplier='PR-20').count(), 1)
        self.assertEqual(response.context['error_count'], 1)
        self.assertContains(response, 'ya aparece en la fila 2')

    def test_messages_reflect_result(self):
        rows = [self.supplier_data('PR-30', email='no-es-correo')]

        response = self.client.post(self.url, {'csv_file': self.csv_file(rows)})

        texts = [str(message) for message in response.context['messages']]
        self.assertEqual(texts, ['1 fila tiene errores y no se registró.'])

    def test_report_keeps_upload_form(self):
        response = self.client.post(self.url, {'csv_file': self.csv_file([self.supplier_data('PR-40')])})
        self.assertIn('csv_file', response.context['form'].fields)

    def test_unknown_status_is_rejected(self):
        response = self.client.post(self.url, {'csv_file': self.csv_file([self.supplier_data('PR-50', status='Pendiente')])})

        self.assertFalse(Suppliers.objects.filter(id_supplier='PR-50').exists())
        self.assertContains(response, '«Pendiente» no existe en el catálogo.')

    def test_country_is_resolved_by_name_or_abbreviation(self):
        rows = [
            self.supplier_data('PR-80', country='mx'),
            self.supplier_data('PR-81', country='CHILE'),
            self.supplier_data('PR-83', country='Chile (CL)'),  # como lo pone la exportación
        ]

        response = self.client.post(self.url, {'csv_file': self.csv_file(rows)})

        self.assertEqual(Suppliers.objects.get(id_supplier='PR-80').country, self.mexico)
        self.assertEqual(Suppliers.objects.get(id_supplier='PR-81').country, self.chile)
        self.assertEqual(Suppliers.objects.get(id_supplier='PR-83').country, self.chile)
        self.assertEqual(response.context['error_count'], 0)

    def test_unknown_country_is_rejected(self):
        response = self.client.post(self.url, {'csv_file': self.csv_file([self.supplier_data('PR-82', country='Mexiko')])})

        self.assertFalse(Suppliers.objects.filter(id_supplier='PR-82').exists())
        self.assertEqual(response.context['error_records'][0]['errors'], {'country': '«Mexiko» no existe en el catálogo.'})

    def test_status_text_is_resolved_to_catalog(self):
        rows = [self.supplier_data('PR-60', status='inactivo'), self.supplier_data('PR-61', status='Active')]

        self.client.post(self.url, {'csv_file': self.csv_file(rows)})

        self.assertEqual(Suppliers.objects.get(id_supplier='PR-60').status, self.inactive)
        self.assertEqual(Suppliers.objects.get(id_supplier='PR-61').status, self.active)
