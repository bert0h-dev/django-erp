from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from core.models import Country, Currency, Status
from users.models import Role, User, UserRole
from .models import Customer

HEADERS = 'id_customer,name,tax_id,country,state,city,address,zip_code,phone,email,payment_terms,currency,payment_method,bank_account,status'


class CustomerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ana', password='Clave-segura-123')
        self.client.force_login(self.user)
        # Los precargan las migraciones core.0002 y core.0004
        self.active = Status.objects.get(name='Activo')
        self.inactive = Status.objects.get(name='Inactivo')
        self.mexico = Country.objects.get(abbreviation='MX')
        self.chile = Country.objects.get(abbreviation='CL')
        self.mxn = Currency.objects.get(code='MXN')
        self.usd = Currency.objects.get(code='USD')

    def set_level(self, level):
        role = Role.objects.create(role_name=f'Clientes {level}', customers=level)
        UserRole.objects.create(user_id=self.user, role=role)

    def post_data(self, code, **fields):
        data = {
            'id_customer': code,
            'name': f'Cliente {code}',
            'tax_id': 'CLI010101ABC',
            'country': self.mexico.pk,
            'city': 'Guadalajara',
            'email': 'compras@cliente.com',
            'currency': self.mxn.pk,
            'status': self.active.pk,
        }
        data.update(fields)
        return data

    def create_customer(self, code, **fields):
        data = {**self.post_data(code), 'country': self.mexico, 'currency': self.mxn, 'status': self.active}
        data.update(fields)
        return Customer.objects.create(**data)

    def upload(self, *rows):
        content = '\n'.join([HEADERS, *rows]).encode('utf-8')
        csv_file = SimpleUploadedFile('clientes.csv', content, content_type='text/csv')
        return self.client.post(reverse('customers:customer_bulk_create'), {'csv_file': csv_file})


class CustomerPermissionTests(CustomerTestCase):
    def setUp(self):
        super().setUp()
        self.customer = self.create_customer('CL-1')
        self.list_url = reverse('customers:customers_list')
        self.edit_url = reverse('customers:customer_edit', args=[self.customer.pk])

    def test_no_access_redirects_to_dashboard(self):
        for url in (self.list_url, reverse('customers:customer_create'), self.edit_url):
            with self.subTest(url=url):
                self.assertRedirects(self.client.get(url), reverse('dashboard'))

    def test_read_only_can_list_but_not_write(self):
        self.set_level(1)

        response = self.client.get(self.list_url)
        self.assertContains(response, 'Cliente CL-1')
        self.assertNotContains(response, 'Crear cliente')

        for url in (reverse('customers:customer_create'), self.edit_url, reverse('customers:customer_bulk_create')):
            with self.subTest(url=url):
                self.assertRedirects(self.client.get(url), self.list_url)

        self.client.post(reverse('customers:customer_delete', args=[self.customer.pk]))
        self.assertTrue(Customer.objects.filter(pk=self.customer.pk).exists())

    def test_read_write_sees_actions(self):
        self.set_level(2)
        response = self.client.get(self.list_url)
        self.assertContains(response, 'Crear cliente')
        self.assertContains(response, self.edit_url)


class CustomerCrudTests(CustomerTestCase):
    def setUp(self):
        super().setUp()
        self.set_level(2)

    def test_create_form_renders_catalogs(self):
        response = self.client.get(reverse('customers:customer_create'))
        self.assertContains(response, 'Nuevo cliente')
        self.assertContains(response, 'México (MX)')
        self.assertContains(response, 'Peso mexicano (MXN)')
        # Un cliente nuevo empieza con el estado activo
        self.assertContains(response, f'value="{self.active.pk}" data-active="true" selected')

    def test_create_assigns_creator_and_catalogs(self):
        response = self.client.post(reverse('customers:customer_create'), self.post_data('CL-9', currency=self.usd.pk))
        self.assertRedirects(response, reverse('customers:customers_list'))

        customer = Customer.objects.get(id_customer='CL-9')
        self.assertEqual(customer.created_by, self.user)
        self.assertEqual(customer.currency, self.usd)
        self.assertEqual(customer.country, self.mexico)

    def test_invalid_create_shows_errors(self):
        response = self.client.post(reverse('customers:customer_create'), self.post_data('', currency=''))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'aria-invalid="true"', count=2)
        self.assertFalse(Customer.objects.exists())

    def test_edit_updates_customer(self):
        customer = self.create_customer('CL-1')
        url = reverse('customers:customer_edit', args=[customer.pk])

        self.assertContains(self.client.get(url), 'Editar Cliente CL-1')
        self.client.post(url, self.post_data('CL-1', name='Nuevo nombre', country=self.chile.pk, status=self.inactive.pk))

        customer.refresh_from_db()
        self.assertEqual(customer.name, 'Nuevo nombre')
        self.assertEqual(customer.country, self.chile)
        self.assertEqual(customer.status, self.inactive)

    def test_delete_removes_customer(self):
        customer = self.create_customer('CL-1')
        self.client.post(reverse('customers:customer_delete', args=[customer.pk]))
        self.assertFalse(Customer.objects.exists())


class CustomerListTests(CustomerTestCase):
    def setUp(self):
        super().setUp()
        self.set_level(1)
        self.create_customer('CL-1')
        self.create_customer('CL-2', country=self.chile, status=self.inactive, currency=self.usd)

    def test_filters(self):
        url = reverse('customers:customers_list')
        cases = [({'country': 'cl'}, 'CL-2', 'CL-1'), ({'status': 'Activo'}, 'CL-1', 'CL-2'), ({'id_customer': '2'}, 'CL-2', 'CL-1')]
        for params, shown, hidden in cases:
            with self.subTest(params=params):
                response = self.client.get(url, params)
                self.assertContains(response, f'Cliente {shown}')
                self.assertNotContains(response, f'Cliente {hidden}')

    def test_summary(self):
        summary = self.client.get(reverse('customers:customers_list')).context['summary']
        self.assertEqual(summary, {'total': 2, 'active': 1, 'inactive': 1, 'countries': 2})

    def test_csv_export(self):
        response = self.client.get(reverse('customers:customers_list'), {'export': 'csv', 'country': 'CL'})
        lines = response.content.decode('utf-8-sig').splitlines()
        self.assertEqual(len(lines), 2)
        self.assertIn('CL-2,Cliente CL-2,CLI010101ABC,CL,', lines[1])
        self.assertIn(',USD,', lines[1])
        self.assertIn(',Inactivo,', lines[1])


class CustomerBulkUploadTests(CustomerTestCase):
    def setUp(self):
        super().setUp()
        self.set_level(2)

    def test_template_has_form_fields(self):
        response = self.client.get(reverse('customers:download_template_customers'))
        self.assertEqual(response.content.decode().strip(), HEADERS)

    def test_upload_page_renders(self):
        response = self.client.get(reverse('customers:customer_bulk_create'))
        self.assertContains(response, 'Carga masiva de clientes')
        self.assertContains(response, 'Monedas (')

    def test_catalogs_resolved_by_name_code_or_both(self):
        response = self.upload(
            'CL-1,Uno,AAA010101AAA,México,,,,,,,,MXN,,,Activo',
            'CL-2,Dos,AAA010101AAA,cl,,,,,,,,dólar estadounidense,,,inactivo',
            'CL-3,Tres,AAA010101AAA,Chile (CL),,,,,,,,Peso chileno (CLP),,,Activo',
        )
        self.assertEqual(response.context['successful_count'], 3)
        self.assertEqual(Customer.objects.get(id_customer='CL-2').currency, self.usd)
        self.assertEqual(Customer.objects.get(id_customer='CL-2').status, self.inactive)
        self.assertEqual(Customer.objects.get(id_customer='CL-3').country, self.chile)
        self.assertTrue(all(c.created_by == self.user for c in Customer.objects.all()))

    def test_errors_are_reported_per_row(self):
        self.create_customer('CL-1')
        response = self.upload(
            'CL-1,Repetido en BD,AAA010101AAA,MX,,,,,,,,MXN,,,Activo',
            'CL-2,País raro,AAA010101AAA,Narnia,,,,,,,,MXN,,,Activo',
            'CL-3,Sin moneda,AAA010101AAA,MX,,,,,,,,,,,Activo',
            'CL-4,Bien,AAA010101AAA,MX,,,,,,,,MXN,,,Activo',
            'CL-4,Repetido en archivo,AAA010101AAA,MX,,,,,,,,MXN,,,Activo',
        )
        self.assertEqual(response.context['successful_count'], 1)
        errors = {record['row']: record['errors'] for record in response.context['error_records']}
        self.assertIn('id_customer', errors[2])
        self.assertEqual(errors[3]['country'], '«Narnia» no existe en el catálogo.')
        self.assertIn('currency', errors[4])
        self.assertIn('fila 5', errors[6]['id_customer'])
        self.assertEqual(Customer.objects.count(), 2)
