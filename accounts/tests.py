from django.test import TestCase
from django.urls import reverse

from .models import User

PASSWORD = 'MotDePasseSolide2026!'


def creer_utilisateur(role, email):
    return User.objects.create_user(email=email, password=PASSWORD, role=role)


class UserManagerTests(TestCase):
    def test_create_user_exige_un_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password=PASSWORD)

    def test_create_superuser_a_le_role_admin(self):
        user = User.objects.create_superuser(email='admin@santesn.sn', password=PASSWORD)
        self.assertEqual(user.role, User.Role.ADMIN)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)


class SetupWizardTests(TestCase):
    def test_wizard_accessible_sans_admin(self):
        response = self.client.get(reverse('accounts:setup_wizard'))
        self.assertEqual(response.status_code, 200)

    def test_login_redirige_vers_wizard_sans_admin(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertRedirects(response, reverse('accounts:setup_wizard'))

    def test_wizard_cree_le_premier_super_admin(self):
        response = self.client.post(reverse('accounts:setup_wizard'), {
            'first_name': 'Awa',
            'last_name': 'Diop',
            'email': 'admin@santesn.sn',
            'phone_number': '770000000',
            'password1': PASSWORD,
            'password2': PASSWORD,
        })
        self.assertRedirects(
            response,
            reverse('accounts:post_login_redirect'),
            target_status_code=302,
        )
        admin = User.objects.get(email='admin@santesn.sn')
        self.assertEqual(admin.role, User.Role.ADMIN)
        self.assertTrue(admin.is_superuser)

    def test_wizard_desactive_apres_creation_admin(self):
        creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')
        response = self.client.get(reverse('accounts:setup_wizard'))
        self.assertRedirects(response, reverse('accounts:login'))


class LoginTests(TestCase):
    def setUp(self):
        self.admin = creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')

    def _login(self, email):
        return self.client.post(reverse('accounts:login'), {
            'email': email,
            'password': PASSWORD,
        })

    def test_connexion_admin_redirige_vers_dashboard_admin(self):
        response = self._login('admin@santesn.sn')
        self.assertRedirects(
            response,
            reverse('accounts:post_login_redirect'),
            target_status_code=302,
        )
        response = self.client.get(reverse('accounts:post_login_redirect'))
        self.assertRedirects(response, reverse('dashboard'))

    def test_connexion_assure_redirige_vers_espace_assure(self):
        creer_utilisateur(User.Role.ASSURE, 'assure@santesn.sn')
        self._login('assure@santesn.sn')
        response = self.client.get(reverse('accounts:post_login_redirect'))
        self.assertRedirects(response, reverse('accounts:dashboard_assure'))

    def test_connexion_medecin_redirige_vers_espace_medecin(self):
        creer_utilisateur(User.Role.MEDECIN, 'medecin@santesn.sn')
        self._login('medecin@santesn.sn')
        response = self.client.get(reverse('accounts:post_login_redirect'))
        self.assertRedirects(response, reverse('accounts:dashboard_medecin'))

    def test_connexion_pharmacien_redirige_vers_espace_pharmacien(self):
        creer_utilisateur(User.Role.PHARMACIEN, 'pharmacien@santesn.sn')
        self._login('pharmacien@santesn.sn')
        response = self.client.get(reverse('accounts:post_login_redirect'))
        self.assertRedirects(response, reverse('accounts:dashboard_pharmacien'))

    def test_mauvais_mot_de_passe_refuse(self):
        response = self.client.post(reverse('accounts:login'), {
            'email': 'admin@santesn.sn',
            'password': 'mauvais',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email ou mot de passe incorrect.')


class ProtectionDesVuesTests(TestCase):
    def setUp(self):
        self.admin = creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')
        self.assure = creer_utilisateur(User.Role.ASSURE, 'assure@santesn.sn')

    def test_dashboard_exige_connexion(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)

    def test_dashboard_interdit_aux_non_admins(self):
        self.client.login(username='assure@santesn.sn', password=PASSWORD)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_dashboard_accessible_a_l_admin(self):
        self.client.login(username='admin@santesn.sn', password=PASSWORD)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_liste_patients_interdite_aux_non_admins(self):
        self.client.login(username='assure@santesn.sn', password=PASSWORD)
        response = self.client.get(reverse('liste_patients'))
        self.assertEqual(response.status_code, 403)

    def test_espace_assure_interdit_au_medecin(self):
        creer_utilisateur(User.Role.MEDECIN, 'medecin@santesn.sn')
        self.client.login(username='medecin@santesn.sn', password=PASSWORD)
        response = self.client.get(reverse('accounts:dashboard_assure'))
        self.assertEqual(response.status_code, 403)
