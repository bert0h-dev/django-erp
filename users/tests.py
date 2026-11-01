from django.test import TestCase
from django.urls import reverse

from .models import Role, User, UserRole
from .permissions import get_module_permission, get_user_permissions, get_user_roles


class PermissionsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ana', password='Clave-segura-123')

    def assign(self, role_name, **levels):
        role = Role.objects.create(role_name=role_name, **levels)
        UserRole.objects.create(user_id=self.user, role=role)
        return role

    def test_user_without_roles_has_no_access(self):
        self.assertEqual(get_user_permissions(self.user), {})
        self.assertEqual(get_module_permission(self.user, 'materials'), 0)
        self.assertEqual(get_user_roles(self.user), [])

    def test_highest_level_across_roles_wins(self):
        self.assign('Lectura', materials=1, sales=2)
        self.assign('Escritura', materials=2, sales=0)

        permissions = get_user_permissions(self.user)

        self.assertEqual(permissions['materials'], 2)
        self.assertEqual(permissions['sales'], 2)
        self.assertNotIn('customers', permissions)
        self.assertEqual(get_module_permission(self.user, 'materials'), 2)
        self.assertCountEqual(get_user_roles(self.user), ['Lectura', 'Escritura'])

    def test_superuser_without_roles_has_no_module_access(self):
        admin = User.objects.create_superuser('root', password='Clave-segura-123')
        self.assertEqual(get_module_permission(admin, 'materials'), 0)


class AuthViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ana', password='Clave-segura-123')

    def test_login_page_renders(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login_with_valid_credentials_redirects_to_dashboard(self):
        response = self.client.post(reverse('login'), {
            'username': 'ana',
            'password': 'Clave-segura-123',
        })
        self.assertRedirects(response, reverse('dashboard'))

    def test_login_with_invalid_credentials_stays_on_login(self):
        response = self.client.post(reverse('login'), {
            'username': 'ana',
            'password': 'incorrecta',
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_authenticated_user_visiting_login_is_redirected(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('login'))
        self.assertRedirects(response, reverse('dashboard'))

    def test_anonymous_user_is_sent_to_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_logout_rejects_get(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)

    def test_logout_with_post(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)


class RoleAdminTests(TestCase):
    def test_role_search(self):
        admin = User.objects.create_superuser('root', password='Clave-segura-123')
        Role.objects.create(role_name='Compras')
        self.client.force_login(admin)

        response = self.client.get('/admin/users/role/', {'q': 'Comp'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Compras')
