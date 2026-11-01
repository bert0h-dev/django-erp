from django.test import TestCase
from django.urls import reverse

from users.models import Role, User, UserRole
from .models import Suppliers


class SupplierTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ana', password='Clave-segura-123')
        self.client.force_login(self.user)

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
            'status': 'Active',
        }
        data.update(fields)
        return data

    def create_supplier(self, code, **fields):
        return Suppliers.objects.create(**self.supplier_data(code, **fields))


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

    def test_create_assigns_creator(self):
        response = self.client.post(reverse('suppliers:supplier_create'), self.supplier_data('PR-2'))

        self.assertRedirects(response, reverse('suppliers:suppliers_list'))
        self.assertEqual(Suppliers.objects.get(id_supplier='PR-2').created_by, self.user)

    def test_invalid_create_shows_errors(self):
        response = self.client.post(reverse('suppliers:supplier_create'), self.supplier_data('PR-3', email='no-es-correo'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'aria-invalid="true"')
        self.assertFalse(Suppliers.objects.filter(id_supplier='PR-3').exists())

    def test_edit_updates_supplier(self):
        supplier = self.create_supplier('PR-4')
        url = reverse('suppliers:supplier_edit', args=[supplier.pk])

        self.assertContains(self.client.get(url), 'Editar Proveedor PR-4')
        response = self.client.post(url, self.supplier_data('PR-4', name='Nuevo nombre'))

        self.assertRedirects(response, reverse('suppliers:suppliers_list'))
        supplier.refresh_from_db()
        self.assertEqual(supplier.name, 'Nuevo nombre')

    def test_delete_removes_supplier(self):
        supplier = self.create_supplier('PR-5')
        response = self.client.post(reverse('suppliers:supplier_delete', args=[supplier.pk]))

        self.assertRedirects(response, reverse('suppliers:suppliers_list'))
        self.assertFalse(Suppliers.objects.filter(pk=supplier.pk).exists())

    def test_country_filter_and_options(self):
        self.create_supplier('PR-6', name='Del norte', country='México')
        self.create_supplier('PR-7', name='Del sur', country='Chile')

        response = self.client.get(reverse('suppliers:suppliers_list'), {'country': 'Chile'})

        self.assertContains(response, 'Del sur')
        self.assertNotContains(response, 'Del norte')
        self.assertContains(response, '<option value="México"')
