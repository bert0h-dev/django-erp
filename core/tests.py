from django.test import TestCase
from django.urls import reverse

from users.models import Role, User, UserRole
from .models import Country, Currency


class DashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ana', password='Clave-segura-123')
        self.client.force_login(self.user)

    def test_dashboard_shows_only_permitted_modules(self):
        role = Role.objects.create(role_name='Almacén', materials=1)
        UserRole.objects.create(user_id=self.user, role=role)

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['permissions']['materials'], 1)
        self.assertNotIn('sales', response.context['permissions'])
        self.assertEqual(response.context['roles'], ['Almacén'])
        self.assertContains(response, reverse('materials:materials_list'))

    def test_dashboard_without_roles_hides_materials(self):
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse('materials:materials_list'))

    def test_menu_logout_uses_post_form(self):
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, f'<form action="{reverse("logout")}" method="post">')


class CatalogTests(TestCase):
    """Catálogos que precargan las migraciones de core."""

    def test_countries_are_loaded_with_iso_codes(self):
        self.assertEqual(Country.objects.count(), 249)
        self.assertEqual(Country.objects.get(abbreviation='MX').name, 'México')
        self.assertEqual(str(Country.objects.get(abbreviation='US')), 'Estados Unidos (US)')

    def test_currencies_are_loaded_and_distinguished_by_code(self):
        self.assertEqual(Currency.objects.filter(symbol='$').count(), 6)
        self.assertEqual(str(Currency.objects.get(code='MXN')), 'Peso mexicano (MXN)')
