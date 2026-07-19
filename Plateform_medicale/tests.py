import datetime
import io
from decimal import Decimal

import openpyxl
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    Consultation,
    Delivrance,
    Medecin,
    Notification,
    Ordonnance,
    Paiement,
    Patient,
    Pharmacien,
    PlanCouverture,
    Prestataire,
    PriseEnCharge,
    RendezVous,
    ServiceMedical,
    User,
    distance_km,
)

PASSWORD = 'MotDePasseSolide2026!'


def creer_utilisateur(role, email):
    return User.objects.create_user(email=email, password=PASSWORD, role=role)


def creer_medecin(email, specialite='Medecine generale'):
    utilisateur = creer_utilisateur(User.Role.MEDECIN, email)
    return Medecin.objects.create(
        user=utilisateur,
        nom='Ndiaye',
        prenom='Awa',
        specialite=specialite,
        telephone='770000000',
        email=email,
    )


def creer_patient(nom='Diop', prenom='Moussa'):
    return Patient.objects.create(
        nom=nom,
        prenom=prenom,
        date_naissance=datetime.date(1990, 1, 1),
        telephone='770000001',
    )


def creer_pharmacien(email):
    utilisateur = creer_utilisateur(User.Role.PHARMACIEN, email)
    return Pharmacien.objects.create(user=utilisateur)


ENTETES_IMPORT_UTILISATEURS = [
    'Email', 'Prenom', 'Nom', 'Telephone', 'Role',
    'Date de naissance', 'Specialite', 'Prestataire', 'Plan de couverture',
]


def creer_fichier_import_utilisateurs(lignes, entetes=None):
    classeur = openpyxl.Workbook()
    feuille = classeur.active
    feuille.append(entetes or ENTETES_IMPORT_UTILISATEURS)
    for ligne in lignes:
        feuille.append(ligne)
    tampon = io.BytesIO()
    classeur.save(tampon)
    tampon.seek(0)
    return SimpleUploadedFile(
        'import.xlsx',
        tampon.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )


def creer_ordonnance(patient, medecin, medicaments='Paracetamol 500mg - 3x/jour'):
    consultation = Consultation.objects.create(
        patient=patient,
        medecin=medecin,
        date_consultation=timezone.now(),
        diagnostic='Diagnostic de test',
    )
    return Ordonnance.objects.create(consultation=consultation, medicaments=medicaments)


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
        response = self.client.get(reverse('setup_wizard'))
        self.assertEqual(response.status_code, 200)

    def test_login_redirige_vers_wizard_sans_admin(self):
        response = self.client.get(reverse('login'))
        self.assertRedirects(response, reverse('setup_wizard'))

    def test_wizard_cree_le_premier_super_admin(self):
        response = self.client.post(reverse('setup_wizard'), {
            'first_name': 'Awa',
            'last_name': 'Diop',
            'email': 'admin@santesn.sn',
            'phone_number': '770000000',
            'password1': PASSWORD,
            'password2': PASSWORD,
        })
        self.assertRedirects(
            response,
            reverse('post_login_redirect'),
            target_status_code=302,
        )
        admin = User.objects.get(email='admin@santesn.sn')
        self.assertEqual(admin.role, User.Role.ADMIN)
        self.assertTrue(admin.is_superuser)

    def test_wizard_desactive_apres_creation_admin(self):
        creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')
        response = self.client.get(reverse('setup_wizard'))
        self.assertRedirects(response, reverse('login'))


class LoginTests(TestCase):
    def setUp(self):
        self.admin = creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')

    def _login(self, email):
        return self.client.post(reverse('login'), {
            'email': email,
            'password': PASSWORD,
        })

    def test_connexion_admin_redirige_vers_dashboard_admin(self):
        response = self._login('admin@santesn.sn')
        self.assertRedirects(
            response,
            reverse('post_login_redirect'),
            target_status_code=302,
        )
        response = self.client.get(reverse('post_login_redirect'))
        self.assertRedirects(response, reverse('dashboard'))

    def test_connexion_assure_redirige_vers_espace_assure(self):
        creer_utilisateur(User.Role.ASSURE, 'assure@santesn.sn')
        self._login('assure@santesn.sn')
        response = self.client.get(reverse('post_login_redirect'))
        self.assertRedirects(
            response,
            reverse('dashboard_assure'),
            target_status_code=302,
        )
        # Sans fiche Patient liee, le premier passage redirige vers la completion du profil.
        response = self.client.get(reverse('dashboard_assure'))
        self.assertRedirects(response, reverse('mon_profil_assure'))

    def test_connexion_medecin_redirige_vers_espace_medecin(self):
        creer_utilisateur(User.Role.MEDECIN, 'medecin@santesn.sn')
        self._login('medecin@santesn.sn')
        response = self.client.get(reverse('post_login_redirect'))
        self.assertRedirects(response, reverse('dashboard_medecin'))

    def test_connexion_pharmacien_redirige_vers_espace_pharmacien(self):
        creer_utilisateur(User.Role.PHARMACIEN, 'pharmacien@santesn.sn')
        self._login('pharmacien@santesn.sn')
        response = self.client.get(reverse('post_login_redirect'))
        self.assertRedirects(response, reverse('dashboard_pharmacien'))

    def test_mauvais_mot_de_passe_refuse(self):
        response = self.client.post(reverse('login'), {
            'email': 'admin@santesn.sn',
            'password': 'mauvais',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email ou mot de passe incorrect.')


class LimitationTentativesConnexionTests(TestCase):
    def setUp(self):
        cache.clear()
        self.admin = creer_utilisateur(User.Role.ADMIN, 'admin-brute@santesn.sn')

    def tearDown(self):
        cache.clear()

    def _mauvais_mot_de_passe(self):
        return self.client.post(reverse('login'), {
            'email': 'admin-brute@santesn.sn',
            'password': 'mauvais',
        })

    def test_blocage_apres_cinq_echecs(self):
        for _ in range(5):
            response = self._mauvais_mot_de_passe()
            self.assertContains(response, 'Email ou mot de passe incorrect.')

        response = self._mauvais_mot_de_passe()
        self.assertContains(response, 'Trop de tentatives de connexion')

    def test_connexion_reussie_reinitialise_le_compteur(self):
        for _ in range(3):
            self._mauvais_mot_de_passe()

        response = self.client.post(reverse('login'), {
            'email': 'admin-brute@santesn.sn',
            'password': PASSWORD,
        })
        self.assertRedirects(response, reverse('post_login_redirect'), target_status_code=302)

        self.client.logout()
        response = self._mauvais_mot_de_passe()
        self.assertContains(response, 'Email ou mot de passe incorrect.')
        self.assertNotContains(response, 'Trop de tentatives de connexion')


class ProtectionDesVuesTests(TestCase):
    def setUp(self):
        self.admin = creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')
        self.assure = creer_utilisateur(User.Role.ASSURE, 'assure@santesn.sn')

    def test_dashboard_exige_connexion(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

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
        response = self.client.get(reverse('dashboard_assure'))
        self.assertEqual(response.status_code, 403)


class GestionUtilisateursTests(TestCase):
    def setUp(self):
        self.admin = creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')
        self.client.login(username='admin@santesn.sn', password=PASSWORD)

    def test_liste_utilisateurs_interdite_aux_non_admins(self):
        self.client.logout()
        creer_utilisateur(User.Role.MEDECIN, 'medecin@santesn.sn')
        self.client.login(username='medecin@santesn.sn', password=PASSWORD)
        response = self.client.get(reverse('liste_utilisateurs'))
        self.assertEqual(response.status_code, 403)

    def test_liste_utilisateurs_accessible_a_l_admin(self):
        response = self.client.get(reverse('liste_utilisateurs'))
        self.assertEqual(response.status_code, 200)

    def test_creation_utilisateur_genere_un_mot_de_passe_fonctionnel(self):
        response = self.client.post(reverse('ajouter_utilisateur'), {
            'first_name': 'Fatou',
            'last_name': 'Ndiaye',
            'email': 'fatou.ndiaye@santesn.sn',
            'phone_number': '770001122',
            'role': User.Role.MEDECIN.value,
        })
        self.assertEqual(response.status_code, 200)
        mot_de_passe = response.context['mot_de_passe']
        utilisateur = User.objects.get(email='fatou.ndiaye@santesn.sn')
        self.assertEqual(utilisateur.role, User.Role.MEDECIN)

        self.client.logout()
        connecte = self.client.login(username='fatou.ndiaye@santesn.sn', password=mot_de_passe)
        self.assertTrue(connecte)

    def test_modification_role_utilisateur(self):
        cible = creer_utilisateur(User.Role.MEDECIN, 'cible@santesn.sn')
        response = self.client.post(reverse('modifier_utilisateur', args=[cible.pk]), {
            'first_name': cible.first_name,
            'last_name': cible.last_name,
            'email': cible.email,
            'phone_number': '',
            'role': User.Role.PHARMACIEN.value,
        })
        self.assertRedirects(response, reverse('liste_utilisateurs'))
        cible.refresh_from_db()
        self.assertEqual(cible.role, User.Role.PHARMACIEN)

    def test_admin_ne_peut_pas_changer_son_propre_role(self):
        response = self.client.post(reverse('modifier_utilisateur', args=[self.admin.pk]), {
            'first_name': self.admin.first_name,
            'last_name': self.admin.last_name,
            'email': self.admin.email,
            'phone_number': '',
            'role': User.Role.MEDECIN.value,
        })
        self.assertEqual(response.status_code, 200)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.role, User.Role.ADMIN)

    def test_desactivation_utilisateur(self):
        cible = creer_utilisateur(User.Role.MEDECIN, 'cible@santesn.sn')
        response = self.client.post(reverse('activer_desactiver_utilisateur', args=[cible.pk]))
        self.assertRedirects(response, reverse('liste_utilisateurs'))
        cible.refresh_from_db()
        self.assertFalse(cible.is_active)

    def test_admin_ne_peut_pas_se_desactiver_lui_meme(self):
        response = self.client.post(reverse('activer_desactiver_utilisateur', args=[self.admin.pk]))
        self.assertRedirects(response, reverse('liste_utilisateurs'))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_admin_ne_peut_pas_se_supprimer_lui_meme(self):
        response = self.client.post(reverse('supprimer_utilisateur', args=[self.admin.pk]))
        self.assertRedirects(response, reverse('liste_utilisateurs'))
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())

    def test_suppression_utilisateur(self):
        cible = creer_utilisateur(User.Role.MEDECIN, 'cible@santesn.sn')
        response = self.client.post(reverse('supprimer_utilisateur', args=[cible.pk]))
        self.assertRedirects(response, reverse('liste_utilisateurs'))
        self.assertFalse(User.objects.filter(pk=cible.pk).exists())

    def test_reinitialisation_mot_de_passe(self):
        cible = creer_utilisateur(User.Role.MEDECIN, 'cible@santesn.sn')
        response = self.client.post(reverse('reinitialiser_mot_de_passe', args=[cible.pk]))
        self.assertEqual(response.status_code, 200)
        nouveau_mot_de_passe = response.context['mot_de_passe']

        self.client.logout()
        connecte = self.client.login(username='cible@santesn.sn', password=nouveau_mot_de_passe)
        self.assertTrue(connecte)

    def test_filtre_par_role(self):
        creer_utilisateur(User.Role.MEDECIN, 'medecin@santesn.sn')
        creer_utilisateur(User.Role.PHARMACIEN, 'pharmacien@santesn.sn')
        response = self.client.get(reverse('liste_utilisateurs'), {'role': User.Role.MEDECIN.value})
        emails = [u.email for u in response.context['utilisateurs']]
        self.assertIn('medecin@santesn.sn', emails)
        self.assertNotIn('pharmacien@santesn.sn', emails)

    def test_filtre_par_statut(self):
        inactif = creer_utilisateur(User.Role.MEDECIN, 'inactif@santesn.sn')
        inactif.is_active = False
        inactif.save(update_fields=['is_active'])
        creer_utilisateur(User.Role.MEDECIN, 'actif@santesn.sn')

        response = self.client.get(reverse('liste_utilisateurs'), {'statut': 'inactif'})
        emails = [u.email for u in response.context['utilisateurs']]
        self.assertIn('inactif@santesn.sn', emails)
        self.assertNotIn('actif@santesn.sn', emails)

    def test_recherche_par_nom_ou_email(self):
        creer_utilisateur(User.Role.MEDECIN, 'ousmane.fall@santesn.sn')
        creer_utilisateur(User.Role.MEDECIN, 'autre@santesn.sn')
        response = self.client.get(reverse('liste_utilisateurs'), {'q': 'ousmane'})
        emails = [u.email for u in response.context['utilisateurs']]
        self.assertIn('ousmane.fall@santesn.sn', emails)
        self.assertNotIn('autre@santesn.sn', emails)


class EspaceMedecinTests(TestCase):
    def setUp(self):
        self.medecin = creer_medecin('medecin1@santesn.sn')
        self.autre_medecin = creer_medecin('medecin2@santesn.sn')
        self.patient = creer_patient()
        self.client.login(username='medecin1@santesn.sn', password=PASSWORD)

    def test_dashboard_interdit_aux_non_medecins(self):
        self.client.logout()
        creer_utilisateur(User.Role.ASSURE, 'assure@santesn.sn')
        self.client.login(username='assure@santesn.sn', password=PASSWORD)
        response = self.client.get(reverse('dashboard_medecin'))
        self.assertEqual(response.status_code, 403)

    def test_dashboard_accessible_au_medecin(self):
        response = self.client.get(reverse('dashboard_medecin'))
        self.assertEqual(response.status_code, 200)

    def test_medecin_sans_fiche_voit_message_dedie(self):
        self.client.logout()
        creer_utilisateur(User.Role.MEDECIN, 'orphelin@santesn.sn')
        self.client.login(username='orphelin@santesn.sn', password=PASSWORD)
        response = self.client.get(reverse('dashboard_medecin'))
        self.assertContains(response, 'pas encore associe')

    def test_creation_rendez_vous_attribue_au_medecin_connecte(self):
        response = self.client.post(reverse('ajouter_rendez_vous'), {
            'patient': self.patient.pk,
            'prestataire': '',
            'date_heure': '2026-08-01T09:30',
            'motif': 'Controle',
        })
        self.assertRedirects(response, reverse('agenda_medecin'))
        rendez_vous = RendezVous.objects.get(patient=self.patient)
        self.assertEqual(rendez_vous.medecin, self.medecin)
        self.assertEqual(rendez_vous.statut, RendezVous.Statut.DEMANDE)

    def test_medecin_ne_peut_pas_modifier_le_rendez_vous_d_un_autre_medecin(self):
        rendez_vous = RendezVous.objects.create(
            patient=self.patient,
            medecin=self.autre_medecin,
            date_heure=timezone.now() + datetime.timedelta(days=1),
        )
        response = self.client.post(
            reverse('changer_statut_rendez_vous', args=[rendez_vous.pk]),
            {'statut': 'CONFIRME'},
        )
        self.assertEqual(response.status_code, 404)
        rendez_vous.refresh_from_db()
        self.assertEqual(rendez_vous.statut, RendezVous.Statut.DEMANDE)

    def test_changement_statut_rendez_vous_propre(self):
        rendez_vous = RendezVous.objects.create(
            patient=self.patient,
            medecin=self.medecin,
            date_heure=timezone.now() + datetime.timedelta(days=1),
        )
        response = self.client.post(
            reverse('changer_statut_rendez_vous', args=[rendez_vous.pk]),
            {'statut': 'CONFIRME'},
        )
        self.assertRedirects(response, reverse('agenda_medecin'))
        rendez_vous.refresh_from_db()
        self.assertEqual(rendez_vous.statut, RendezVous.Statut.CONFIRME)

    def test_creation_consultation_et_ordonnance_avec_qr(self):
        response = self.client.post(reverse('ajouter_consultation_medecin'), {
            'patient': self.patient.pk,
            'service': '',
            'prise_en_charge': '',
            'date_consultation': '2026-08-01T10:00',
            'diagnostic': 'Grippe saisonniere',
            'traitement': 'Repos et paracetamol',
        })
        consultation = Consultation.objects.get(patient=self.patient)
        self.assertEqual(consultation.medecin, self.medecin)
        self.assertRedirects(
            response,
            reverse('ajouter_ordonnance_medecin', args=[consultation.pk]),
        )

        response = self.client.post(
            reverse('ajouter_ordonnance_medecin', args=[consultation.pk]),
            {'medicaments': 'Paracetamol 500mg - 3x/jour pendant 5 jours'},
        )
        ordonnance = Ordonnance.objects.get(consultation=consultation)
        self.assertTrue(ordonnance.code_qr.startswith('RX-'))
        self.assertRedirects(
            response,
            reverse('voir_ordonnance_medecin', args=[ordonnance.pk]),
        )

        reponse_qr = self.client.get(reverse('voir_ordonnance_medecin', args=[ordonnance.pk]))
        self.assertContains(reponse_qr, '<svg')

    def test_medecin_ne_peut_pas_creer_ordonnance_pour_consultation_d_un_autre(self):
        consultation_autre = Consultation.objects.create(
            patient=self.patient,
            medecin=self.autre_medecin,
            date_consultation=timezone.now(),
            diagnostic='Diagnostic confidentiel',
        )
        response = self.client.get(
            reverse('ajouter_ordonnance_medecin', args=[consultation_autre.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_mes_patients_scope_au_medecin_connecte(self):
        autre_patient = creer_patient(nom='Sow', prenom='Fatou')
        Consultation.objects.create(
            patient=self.patient,
            medecin=self.medecin,
            date_consultation=timezone.now(),
            diagnostic='RAS',
        )
        Consultation.objects.create(
            patient=autre_patient,
            medecin=self.autre_medecin,
            date_consultation=timezone.now(),
            diagnostic='RAS',
        )
        response = self.client.get(reverse('mes_patients'))
        patients = list(response.context['patients'])
        self.assertIn(self.patient, patients)
        self.assertNotIn(autre_patient, patients)

    def test_modification_profil_medecin_ne_touche_pas_email(self):
        response = self.client.post(reverse('modifier_profil_medecin'), {
            'specialite': 'Cardiologie',
            'telephone': '781234567',
        })
        self.assertRedirects(response, reverse('modifier_profil_medecin'))
        self.medecin.refresh_from_db()
        self.assertEqual(self.medecin.specialite, 'Cardiologie')
        self.assertEqual(self.medecin.telephone, '781234567')
        self.assertEqual(self.medecin.email, 'medecin1@santesn.sn')


class EspacePharmacienTests(TestCase):
    def setUp(self):
        self.pharmacien = creer_pharmacien('pharmacien1@santesn.sn')
        self.medecin = creer_medecin('medecin-rx@santesn.sn')
        self.patient = creer_patient()
        self.ordonnance = creer_ordonnance(self.patient, self.medecin)
        self.client.login(username='pharmacien1@santesn.sn', password=PASSWORD)

    def test_dashboard_interdit_aux_non_pharmaciens(self):
        self.client.logout()
        creer_utilisateur(User.Role.ASSURE, 'assure@santesn.sn')
        self.client.login(username='assure@santesn.sn', password=PASSWORD)
        response = self.client.get(reverse('dashboard_pharmacien'))
        self.assertEqual(response.status_code, 403)

    def test_dashboard_accessible_au_pharmacien(self):
        response = self.client.get(reverse('dashboard_pharmacien'))
        self.assertEqual(response.status_code, 200)

    def test_scan_code_valide_affiche_ordonnance(self):
        response = self.client.post(reverse('scanner_ordonnance'), {
            'code_qr': self.ordonnance.code_qr,
        })
        self.assertEqual(response.context['ordonnance'], self.ordonnance)
        self.assertContains(response, self.patient.nom)

    def test_scan_code_invalide_affiche_erreur(self):
        response = self.client.post(reverse('scanner_ordonnance'), {
            'code_qr': 'RX-INEXISTANT',
        })
        self.assertIsNone(response.context['ordonnance'])
        self.assertContains(response, 'Aucune ordonnance ne correspond a ce code.')

    def test_validation_delivrance(self):
        response = self.client.post(reverse('valider_delivrance', args=[self.ordonnance.pk]))
        self.assertRedirects(response, reverse('historique_delivrances'))
        delivrance = Delivrance.objects.get(ordonnance=self.ordonnance)
        self.assertEqual(delivrance.pharmacien, self.pharmacien)

    def test_double_delivrance_refusee(self):
        Delivrance.objects.create(ordonnance=self.ordonnance, pharmacien=self.pharmacien)
        response = self.client.post(reverse('valider_delivrance', args=[self.ordonnance.pk]))
        self.assertRedirects(response, reverse('historique_delivrances'))
        self.assertEqual(Delivrance.objects.filter(ordonnance=self.ordonnance).count(), 1)

    def test_historique_scope_au_pharmacien_connecte(self):
        autre_pharmacien = creer_pharmacien('pharmacien2@santesn.sn')
        autre_ordonnance = creer_ordonnance(creer_patient(nom='Sow', prenom='Awa'), self.medecin)
        Delivrance.objects.create(ordonnance=self.ordonnance, pharmacien=self.pharmacien)
        Delivrance.objects.create(ordonnance=autre_ordonnance, pharmacien=autre_pharmacien)

        response = self.client.get(reverse('historique_delivrances'))
        delivrances = list(response.context['delivrances'])
        self.assertEqual(len(delivrances), 1)
        self.assertEqual(delivrances[0].ordonnance, self.ordonnance)


class EspaceAssureTests(TestCase):
    def setUp(self):
        self.utilisateur = creer_utilisateur(User.Role.ASSURE, 'assure1@santesn.sn')
        self.client.login(username='assure1@santesn.sn', password=PASSWORD)

    def _completer_profil(self):
        self.client.post(reverse('mon_profil_assure'), {
            'nom': 'Diop',
            'prenom': 'Moussa',
            'date_naissance': '1988-04-12',
            'telephone': '770001122',
            'adresse': 'Dakar',
        })
        return Patient.objects.get(user=self.utilisateur)

    def test_dashboard_interdit_aux_non_assures(self):
        self.client.logout()
        creer_utilisateur(User.Role.MEDECIN, 'medecin@santesn.sn')
        self.client.login(username='medecin@santesn.sn', password=PASSWORD)
        response = self.client.get(reverse('dashboard_assure'))
        self.assertEqual(response.status_code, 403)

    def test_dashboard_redirige_vers_profil_sans_fiche(self):
        response = self.client.get(reverse('dashboard_assure'))
        self.assertRedirects(response, reverse('mon_profil_assure'))

    def test_completion_profil_cree_patient_principal(self):
        patient = self._completer_profil()
        self.assertEqual(patient.type_beneficiaire, Patient.TypeBeneficiaire.PRINCIPAL)
        self.assertTrue(patient.numero_carte)
        response = self.client.get(reverse('dashboard_assure'))
        self.assertEqual(response.status_code, 200)

    def test_ajout_ayant_droit(self):
        patient = self._completer_profil()
        response = self.client.post(reverse('ajouter_ayant_droit'), {
            'nom': 'Diop',
            'prenom': 'Fatou',
            'date_naissance': '2015-06-01',
            'telephone': '',
            'lien_parente': 'ENFANT',
        })
        self.assertRedirects(response, reverse('liste_ayants_droit'))
        ayant_droit = Patient.objects.get(nom='Diop', prenom='Fatou')
        self.assertEqual(ayant_droit.assure_principal, patient)
        self.assertEqual(ayant_droit.type_beneficiaire, Patient.TypeBeneficiaire.AYANT_DROIT)
        self.assertNotEqual(ayant_droit.numero_carte, patient.numero_carte)

    def test_ayant_droit_herite_du_plan_de_couverture(self):
        plan = PlanCouverture.objects.create(nom='Standard', taux_couverture=Decimal('80.00'))
        patient = self._completer_profil()
        patient.plan_couverture = plan
        patient.save(update_fields=['plan_couverture'])

        self.client.post(reverse('ajouter_ayant_droit'), {
            'nom': 'Diop', 'prenom': 'Fatou', 'date_naissance': '2015-06-01',
            'telephone': '', 'lien_parente': 'ENFANT',
        })
        ayant_droit = Patient.objects.get(nom='Diop', prenom='Fatou')
        self.assertEqual(ayant_droit.taux_couverture, plan.taux_couverture)

    def test_assure_ne_peut_pas_modifier_ayant_droit_dun_autre_compte(self):
        self._completer_profil()
        autre_assure = creer_utilisateur(User.Role.ASSURE, 'assure2@santesn.sn')
        autre_patient = Patient.objects.create(
            user=autre_assure, nom='Sow', prenom='Awa',
            date_naissance=datetime.date(1980, 1, 1), telephone='770000002',
        )
        autre_ayant_droit = Patient.objects.create(
            nom='Sow', prenom='Ibra', date_naissance=datetime.date(2010, 1, 1),
            telephone='', type_beneficiaire=Patient.TypeBeneficiaire.AYANT_DROIT,
            assure_principal=autre_patient,
        )
        response = self.client.get(reverse('modifier_ayant_droit', args=[autre_ayant_droit.pk]))
        self.assertEqual(response.status_code, 404)

    def test_suppression_ayant_droit(self):
        self._completer_profil()
        self.client.post(reverse('ajouter_ayant_droit'), {
            'nom': 'Diop', 'prenom': 'Fatou', 'date_naissance': '2015-06-01',
            'telephone': '', 'lien_parente': 'ENFANT',
        })
        ayant_droit = Patient.objects.get(nom='Diop', prenom='Fatou')
        response = self.client.post(reverse('supprimer_ayant_droit', args=[ayant_droit.pk]))
        self.assertRedirects(response, reverse('liste_ayants_droit'))
        self.assertFalse(Patient.objects.filter(pk=ayant_droit.pk).exists())

    def test_assure_ne_peut_pas_supprimer_ayant_droit_dun_autre_compte(self):
        self._completer_profil()
        autre_assure = creer_utilisateur(User.Role.ASSURE, 'assure2@santesn.sn')
        autre_patient = Patient.objects.create(
            user=autre_assure, nom='Sow', prenom='Awa',
            date_naissance=datetime.date(1980, 1, 1), telephone='770000002',
        )
        autre_ayant_droit = Patient.objects.create(
            nom='Sow', prenom='Ibra', date_naissance=datetime.date(2010, 1, 1),
            telephone='', type_beneficiaire=Patient.TypeBeneficiaire.AYANT_DROIT,
            assure_principal=autre_patient,
        )
        response = self.client.post(reverse('supprimer_ayant_droit', args=[autre_ayant_droit.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Patient.objects.filter(pk=autre_ayant_droit.pk).exists())

    def test_creation_rendez_vous_pour_beneficiaire(self):
        patient = self._completer_profil()
        medecin = creer_medecin('medecin-rdv@santesn.sn')
        response = self.client.post(reverse('ajouter_rendez_vous_assure'), {
            'patient': patient.pk,
            'medecin': medecin.pk,
            'prestataire': '',
            'date_heure': '2026-09-01T09:00',
            'motif': 'Controle',
        })
        self.assertRedirects(response, reverse('mes_rendez_vous_assure'))
        rendez_vous = RendezVous.objects.get(patient=patient)
        self.assertEqual(rendez_vous.medecin, medecin)
        self.assertEqual(rendez_vous.statut, RendezVous.Statut.DEMANDE)

    def test_ne_peut_pas_prendre_rendez_vous_pour_un_patient_hors_famille(self):
        self._completer_profil()
        medecin = creer_medecin('medecin-rdv2@santesn.sn')
        autre_patient = creer_patient(nom='Sow', prenom='Awa')
        response = self.client.post(reverse('ajouter_rendez_vous_assure'), {
            'patient': autre_patient.pk,
            'medecin': medecin.pk,
            'prestataire': '',
            'date_heure': '2026-09-01T09:00',
            'motif': 'Controle',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(RendezVous.objects.filter(patient=autre_patient).exists())

    def test_annulation_rendez_vous(self):
        patient = self._completer_profil()
        medecin = creer_medecin('medecin-rdv3@santesn.sn')
        rendez_vous = RendezVous.objects.create(
            patient=patient, medecin=medecin,
            date_heure=timezone.now() + datetime.timedelta(days=1),
        )
        response = self.client.post(reverse('annuler_rendez_vous_assure', args=[rendez_vous.pk]))
        self.assertRedirects(response, reverse('mes_rendez_vous_assure'))
        rendez_vous.refresh_from_db()
        self.assertEqual(rendez_vous.statut, RendezVous.Statut.ANNULE)

    def test_ordonnances_et_historique_scopes_a_la_famille(self):
        patient = self._completer_profil()
        medecin = creer_medecin('medecin-rdv4@santesn.sn')
        ordonnance = creer_ordonnance(patient, medecin)

        autre_patient = creer_patient(nom='Kane', prenom='Modou')
        creer_ordonnance(autre_patient, medecin)

        response = self.client.get(reverse('mes_ordonnances_assure'))
        ordonnances = list(response.context['ordonnances'])
        self.assertEqual(ordonnances, [ordonnance])

        response = self.client.get(reverse('mon_historique_assure'))
        consultations = list(response.context['consultations'])
        self.assertEqual([c.patient for c in consultations], [patient])

    def test_ne_peut_pas_voir_ordonnance_dun_autre_foyer(self):
        self._completer_profil()
        medecin = creer_medecin('medecin-rdv5@santesn.sn')
        autre_patient = creer_patient(nom='Kane', prenom='Modou')
        autre_ordonnance = creer_ordonnance(autre_patient, medecin)

        response = self.client.get(reverse('voir_ordonnance_assure', args=[autre_ordonnance.pk]))
        self.assertEqual(response.status_code, 404)


class AdminPrestatairesTests(TestCase):
    def setUp(self):
        self.admin = creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')
        self.client.login(username='admin@santesn.sn', password=PASSWORD)

    def test_liste_prestataires_interdite_aux_non_admins(self):
        self.client.logout()
        creer_utilisateur(User.Role.MEDECIN, 'medecin@santesn.sn')
        self.client.login(username='medecin@santesn.sn', password=PASSWORD)
        response = self.client.get(reverse('liste_prestataires'))
        self.assertEqual(response.status_code, 403)

    def test_creation_prestataire(self):
        response = self.client.post(reverse('ajouter_prestataire'), {
            'nom': 'Clinique Pasteur',
            'type_prestataire': 'CLINIQUE',
            'adresse': 'Dakar',
            'ville': 'Dakar',
            'telephone': '338000000',
            'partenaire': 'on',
            'date_conventionnement': '',
        })
        self.assertRedirects(response, reverse('liste_prestataires'))
        self.assertTrue(Prestataire.objects.filter(nom='Clinique Pasteur').exists())

    def test_modification_et_suppression_prestataire(self):
        prestataire = Prestataire.objects.create(nom='Hopital Test', type_prestataire='HOPITAL')
        response = self.client.post(reverse('modifier_prestataire', args=[prestataire.pk]), {
            'nom': 'Hopital Renomme',
            'type_prestataire': 'HOPITAL',
            'adresse': '', 'ville': '', 'telephone': '',
            'partenaire': 'on', 'date_conventionnement': '',
        })
        self.assertRedirects(response, reverse('liste_prestataires'))
        prestataire.refresh_from_db()
        self.assertEqual(prestataire.nom, 'Hopital Renomme')

        response = self.client.post(reverse('supprimer_prestataire', args=[prestataire.pk]))
        self.assertRedirects(response, reverse('liste_prestataires'))
        self.assertFalse(Prestataire.objects.filter(pk=prestataire.pk).exists())


class DistanceKmTests(TestCase):
    def test_meme_point_distance_nulle(self):
        self.assertEqual(distance_km(14.6928, -17.4467, 14.6928, -17.4467), 0)

    def test_un_degre_de_latitude(self):
        resultat = distance_km(0, 0, 1, 0)
        self.assertAlmostEqual(resultat, 111.19, delta=0.5)

    def test_un_degre_de_longitude_a_l_equateur(self):
        resultat = distance_km(0, 0, 0, 1)
        self.assertAlmostEqual(resultat, 111.19, delta=0.5)


class PrestataireCoordonneesTests(TestCase):
    def setUp(self):
        self.admin = creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')
        self.client.login(username='admin@santesn.sn', password=PASSWORD)

    def test_creation_prestataire_avec_coordonnees(self):
        response = self.client.post(reverse('ajouter_prestataire'), {
            'nom': 'Hopital Principal', 'type_prestataire': 'HOPITAL',
            'adresse': 'Dakar', 'ville': 'Dakar', 'telephone': '338000001',
            'partenaire': 'on', 'date_conventionnement': '',
            'latitude': '14.6928', 'longitude': '-17.4467',
        })
        self.assertRedirects(response, reverse('liste_prestataires'))
        prestataire = Prestataire.objects.get(nom='Hopital Principal')
        self.assertAlmostEqual(float(prestataire.latitude), 14.6928, places=4)
        self.assertAlmostEqual(float(prestataire.longitude), -17.4467, places=4)

    def test_creation_prestataire_sans_coordonnees_reste_valide(self):
        response = self.client.post(reverse('ajouter_prestataire'), {
            'nom': 'Cabinet Sans Pin', 'type_prestataire': 'CABINET',
            'adresse': '', 'ville': '', 'telephone': '',
            'partenaire': 'on', 'date_conventionnement': '',
            'latitude': '', 'longitude': '',
        })
        self.assertRedirects(response, reverse('liste_prestataires'))
        prestataire = Prestataire.objects.get(nom='Cabinet Sans Pin')
        self.assertIsNone(prestataire.latitude)
        self.assertIsNone(prestataire.longitude)


class AdminPharmaciensTests(TestCase):
    def setUp(self):
        self.admin = creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')
        self.client.login(username='admin@santesn.sn', password=PASSWORD)

    def test_affectation_pharmacien_a_une_pharmacie(self):
        pharmacien = creer_pharmacien('pharmacien@santesn.sn')
        pharmacie = Prestataire.objects.create(nom='Pharmacie Centrale', type_prestataire='PHARMACIE')
        response = self.client.post(reverse('modifier_pharmacien', args=[pharmacien.pk]), {
            'prestataire': pharmacie.pk,
        })
        self.assertRedirects(response, reverse('liste_pharmaciens'))
        pharmacien.refresh_from_db()
        self.assertEqual(pharmacien.prestataire, pharmacie)


class AdminPatientFormTests(TestCase):
    def setUp(self):
        self.admin = creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')
        self.client.login(username='admin@santesn.sn', password=PASSWORD)

    def test_admin_peut_attribuer_un_plan_de_couverture(self):
        patient = creer_patient()
        plan = PlanCouverture.objects.create(nom='Premium', taux_couverture=Decimal('90.00'))
        response = self.client.post(reverse('modifier_patient', args=[patient.pk]), {
            'nom': patient.nom, 'prenom': patient.prenom,
            'date_naissance': '1990-01-01', 'telephone': patient.telephone, 'adresse': '',
            'type_beneficiaire': 'PRINCIPAL', 'assure_principal': '', 'lien_parente': '',
            'plan_couverture': plan.pk,
        })
        self.assertRedirects(response, reverse('liste_patients'))
        patient.refresh_from_db()
        self.assertEqual(patient.plan_couverture, plan)

    def test_filtre_liste_patients_par_type(self):
        principal = creer_patient(nom='Diop', prenom='Moussa')
        Patient.objects.create(
            nom='Diop', prenom='Petit', date_naissance=datetime.date(2015, 1, 1),
            type_beneficiaire=Patient.TypeBeneficiaire.AYANT_DROIT, assure_principal=principal,
        )
        response = self.client.get(reverse('liste_patients'), {'type': 'AYANT_DROIT'})
        patients = list(response.context['patients'])
        self.assertEqual(len(patients), 1)
        self.assertEqual(patients[0].prenom, 'Petit')

    def test_creation_assure_principal_cree_son_compte(self):
        response = self.client.post(reverse('ajouter_patient'), {
            'nom': 'Ndiaye', 'prenom': 'Fatou', 'date_naissance': '1985-05-05',
            'telephone': '', 'adresse': '', 'type_beneficiaire': 'PRINCIPAL',
            'assure_principal': '', 'lien_parente': '', 'plan_couverture': '',
            'email': 'fatou.ndiaye@santesn.sn',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'fatou.ndiaye@santesn.sn')
        patient = Patient.objects.get(nom='Ndiaye')
        self.assertIsNotNone(patient.user)
        self.assertEqual(patient.user.role, User.Role.ASSURE)

    def test_creation_assure_principal_sans_email_refuse(self):
        response = self.client.post(reverse('ajouter_patient'), {
            'nom': 'Ndiaye', 'prenom': 'Fatou', 'date_naissance': '1985-05-05',
            'telephone': '', 'adresse': '', 'type_beneficiaire': 'PRINCIPAL',
            'assure_principal': '', 'lien_parente': '', 'plan_couverture': '', 'email': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Patient.objects.filter(nom='Ndiaye').exists())

    def test_creation_ayant_droit_ne_cree_pas_de_compte(self):
        principal = creer_patient(nom='Diop', prenom='Moussa')
        response = self.client.post(reverse('ajouter_patient'), {
            'nom': 'Diop', 'prenom': 'Petit', 'date_naissance': '2015-01-01',
            'telephone': '', 'adresse': '', 'type_beneficiaire': 'AYANT_DROIT',
            'assure_principal': principal.pk, 'lien_parente': 'ENFANT', 'plan_couverture': '',
            'email': '',
        })
        self.assertRedirects(response, reverse('liste_patients'))
        ayant_droit = Patient.objects.get(nom='Diop', prenom='Petit')
        self.assertIsNone(ayant_droit.user)

    def test_suppression_assure_principal_desactive_le_compte_lie(self):
        utilisateur = creer_utilisateur(User.Role.ASSURE, 'assure.a.supprimer@santesn.sn')
        patient = Patient.objects.create(
            user=utilisateur, nom='Sarr', prenom='Khady',
            date_naissance=datetime.date(1990, 1, 1), telephone='770000009',
        )
        self.assertTrue(utilisateur.is_active)
        response = self.client.post(reverse('supprimer_patient', args=[patient.pk]))
        self.assertRedirects(response, reverse('liste_patients'))
        utilisateur.refresh_from_db()
        self.assertFalse(utilisateur.is_active)

    def test_suppression_ayant_droit_par_admin_ne_touche_aucun_compte(self):
        principal = creer_patient(nom='Diop', prenom='Moussa')
        ayant_droit = Patient.objects.create(
            nom='Diop', prenom='Petit', date_naissance=datetime.date(2015, 1, 1),
            type_beneficiaire=Patient.TypeBeneficiaire.AYANT_DROIT, assure_principal=principal,
        )
        response = self.client.post(reverse('supprimer_patient', args=[ayant_droit.pk]))
        self.assertRedirects(response, reverse('liste_patients'))
        self.assertFalse(Patient.objects.filter(pk=ayant_droit.pk).exists())


class NotificationsTests(TestCase):
    def setUp(self):
        self.admin = creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')
        self.client.login(username='admin@santesn.sn', password=PASSWORD)

    def test_envoi_a_un_utilisateur_precis(self):
        medecin_user = creer_utilisateur(User.Role.MEDECIN, 'medecin@santesn.sn')
        response = self.client.post(reverse('envoyer_notification'), {
            'destinataire': medecin_user.pk,
            'role': '',
            'message': 'Reunion demain a 9h',
        })
        self.assertRedirects(response, reverse('liste_notifications_envoyees'))
        self.assertEqual(Notification.objects.filter(destinataire=medecin_user).count(), 1)

    def test_envoi_a_tout_un_role(self):
        creer_utilisateur(User.Role.MEDECIN, 'medecin1@santesn.sn')
        creer_utilisateur(User.Role.MEDECIN, 'medecin2@santesn.sn')
        creer_utilisateur(User.Role.PHARMACIEN, 'pharmacien1@santesn.sn')

        response = self.client.post(reverse('envoyer_notification'), {
            'destinataire': '',
            'role': User.Role.MEDECIN.value,
            'message': 'Mise a jour du protocole',
        })
        self.assertRedirects(response, reverse('liste_notifications_envoyees'))
        self.assertEqual(Notification.objects.count(), 2)

    def test_ni_destinataire_ni_role_refuse(self):
        response = self.client.post(reverse('envoyer_notification'), {
            'destinataire': '', 'role': '', 'message': 'Test',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Notification.objects.count(), 0)

    def test_utilisateur_voit_et_marque_lue_sa_propre_notification(self):
        medecin_user = creer_utilisateur(User.Role.MEDECIN, 'medecin@santesn.sn')
        notification = Notification.objects.create(destinataire=medecin_user, message='Bienvenue')

        self.client.logout()
        self.client.login(username='medecin@santesn.sn', password=PASSWORD)
        response = self.client.get(reverse('mes_notifications'))
        self.assertContains(response, 'Bienvenue')

        response = self.client.post(reverse('marquer_notification_lue', args=[notification.pk]))
        self.assertRedirects(response, reverse('mes_notifications'))
        notification.refresh_from_db()
        self.assertTrue(notification.lue)

    def test_ne_peut_pas_marquer_la_notification_dun_autre(self):
        medecin_user = creer_utilisateur(User.Role.MEDECIN, 'medecin@santesn.sn')
        autre_user = creer_utilisateur(User.Role.PHARMACIEN, 'pharmacien@santesn.sn')
        notification = Notification.objects.create(destinataire=medecin_user, message='Confidentiel')

        self.client.logout()
        self.client.login(username='pharmacien@santesn.sn', password=PASSWORD)
        response = self.client.post(reverse('marquer_notification_lue', args=[notification.pk]))
        self.assertEqual(response.status_code, 404)


class RapportsTests(TestCase):
    def setUp(self):
        self.admin = creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')
        self.client.login(username='admin@santesn.sn', password=PASSWORD)

    def test_rapports_interdit_aux_non_admins(self):
        self.client.logout()
        creer_utilisateur(User.Role.MEDECIN, 'medecin@santesn.sn')
        self.client.login(username='medecin@santesn.sn', password=PASSWORD)
        response = self.client.get(reverse('rapports'))
        self.assertEqual(response.status_code, 403)

    def test_rapports_accessible_a_l_admin(self):
        creer_utilisateur(User.Role.MEDECIN, 'medecin@santesn.sn')
        response = self.client.get(reverse('rapports'))
        self.assertEqual(response.status_code, 200)
        roles = {ligne['label']: ligne['total'] for ligne in response.context['utilisateurs_par_role']}
        self.assertEqual(roles['Médecin'], 1)

    def test_rapports_inclut_consultations_par_mois(self):
        patient = creer_patient()
        medecin = creer_medecin('medecin@santesn.sn')
        Consultation.objects.create(
            patient=patient,
            medecin=medecin,
            date_consultation=timezone.now(),
            diagnostic='Controle',
        )
        response = self.client.get(reverse('rapports'))
        donnees = response.context['consultations_par_mois']
        self.assertEqual(len(donnees['labels']), 6)
        self.assertEqual(len(donnees['totaux']), 6)
        self.assertEqual(donnees['totaux'][-1], 1)

    def test_export_rapports_excel_interdit_aux_non_admins(self):
        self.client.logout()
        creer_utilisateur(User.Role.MEDECIN, 'medecin@santesn.sn')
        self.client.login(username='medecin@santesn.sn', password=PASSWORD)
        response = self.client.get(reverse('exporter_rapports_excel'))
        self.assertEqual(response.status_code, 403)

    def test_export_rapports_excel_contient_un_onglet_par_tableau(self):
        creer_utilisateur(User.Role.MEDECIN, 'medecin@santesn.sn')
        response = self.client.get(reverse('exporter_rapports_excel'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        self.assertIn('attachment', response['Content-Disposition'])

        classeur = openpyxl.load_workbook(io.BytesIO(response.content))
        self.assertEqual(
            classeur.sheetnames,
            [
                'Chiffres cles',
                'Utilisateurs par role',
                'Assures par type',
                'Rendez-vous par statut',
                'Prises en charge par statut',
                'Consultations par mois',
            ],
        )
        feuille_roles = classeur['Utilisateurs par role']
        lignes = {ligne[0].value: ligne[1].value for ligne in feuille_roles.iter_rows(min_row=2)}
        self.assertEqual(lignes['Médecin'], 1)

    def test_export_rapports_pdf_interdit_aux_non_admins(self):
        self.client.logout()
        creer_utilisateur(User.Role.MEDECIN, 'medecin@santesn.sn')
        self.client.login(username='medecin@santesn.sn', password=PASSWORD)
        response = self.client.get(reverse('exporter_rapports_pdf'))
        self.assertEqual(response.status_code, 403)

    def test_export_rapports_pdf_genere_un_fichier_pdf(self):
        response = self.client.get(reverse('exporter_rapports_pdf'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF'))


class AdminMedecinsFormTests(TestCase):
    def setUp(self):
        self.admin = creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')
        self.client.login(username='admin@santesn.sn', password=PASSWORD)

    def test_creation_medecin_via_formulaire_cree_aussi_son_compte(self):
        response = self.client.post(reverse('ajouter_medecin'), {
            'nom': 'Sarr', 'prenom': 'Ibrahima', 'specialite': 'Pediatrie',
            'telephone': '770001122', 'email': 'ibrahima.sarr@santesn.sn', 'prestataire': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ibrahima.sarr@santesn.sn')
        medecin = Medecin.objects.get(email='ibrahima.sarr@santesn.sn')
        self.assertIsNotNone(medecin.user)
        self.assertEqual(medecin.user.email, 'ibrahima.sarr@santesn.sn')
        self.assertEqual(medecin.user.role, User.Role.MEDECIN)
        self.assertTrue(User.objects.filter(email='ibrahima.sarr@santesn.sn').exists())

    def test_email_duplique_refuse_proprement(self):
        Medecin.objects.create(
            nom='Ba', prenom='Ousmane', specialite='Cardiologie',
            telephone='770002233', email='dup@santesn.sn',
        )
        response = self.client.post(reverse('ajouter_medecin'), {
            'nom': 'Diop', 'prenom': 'Awa', 'specialite': 'Dermatologie',
            'telephone': '770003344', 'email': 'dup@santesn.sn', 'prestataire': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Medecin.objects.filter(nom='Diop').exists())

    def test_email_deja_utilise_par_un_compte_refuse(self):
        creer_utilisateur(User.Role.ASSURE, 'compte.existant@santesn.sn')
        response = self.client.post(reverse('ajouter_medecin'), {
            'nom': 'Diop', 'prenom': 'Awa', 'specialite': 'Dermatologie',
            'telephone': '770003344', 'email': 'compte.existant@santesn.sn', 'prestataire': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Medecin.objects.filter(nom='Diop').exists())

    def test_modification_et_suppression_medecin(self):
        medecin = Medecin.objects.create(
            nom='Fall', prenom='Modou', specialite='Generaliste',
            telephone='770004455', email='fall@santesn.sn',
        )
        response = self.client.post(reverse('modifier_medecin', args=[medecin.pk]), {
            'nom': 'Fall', 'prenom': 'Modou', 'specialite': 'Chirurgie',
            'telephone': '770004455', 'email': 'fall@santesn.sn', 'prestataire': '',
        })
        self.assertRedirects(response, reverse('liste_medecins'))
        medecin.refresh_from_db()
        self.assertEqual(medecin.specialite, 'Chirurgie')

        response = self.client.post(reverse('supprimer_medecin', args=[medecin.pk]))
        self.assertRedirects(response, reverse('liste_medecins'))
        self.assertFalse(Medecin.objects.filter(pk=medecin.pk).exists())

    def test_modifier_medecin_inexistant_donne_404(self):
        response = self.client.get(reverse('modifier_medecin', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_suppression_medecin_desactive_le_compte_lie(self):
        medecin = creer_medecin('medecin.a.supprimer@santesn.sn')
        utilisateur = medecin.user
        self.assertTrue(utilisateur.is_active)
        response = self.client.post(reverse('supprimer_medecin', args=[medecin.pk]))
        self.assertRedirects(response, reverse('liste_medecins'))
        utilisateur.refresh_from_db()
        self.assertFalse(utilisateur.is_active)


class AdminServicesFormTests(TestCase):
    def setUp(self):
        self.admin = creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')
        self.client.login(username='admin@santesn.sn', password=PASSWORD)

    def test_creation_et_suppression_service(self):
        response = self.client.post(reverse('ajouter_service'), {
            'nom': 'Radiographie', 'description': 'Radio standard', 'prix': '15000', 'prestataire': '',
        })
        self.assertRedirects(response, reverse('liste_services'))
        service = ServiceMedical.objects.get(nom='Radiographie')

        response = self.client.post(reverse('supprimer_service', args=[service.pk]))
        self.assertRedirects(response, reverse('liste_services'))
        self.assertFalse(ServiceMedical.objects.filter(pk=service.pk).exists())

    def test_prix_invalide_refuse_proprement(self):
        response = self.client.post(reverse('ajouter_service'), {
            'nom': 'Analyse', 'description': '', 'prix': 'gratuit', 'prestataire': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ServiceMedical.objects.filter(nom='Analyse').exists())

    def test_supprimer_service_inexistant_donne_404(self):
        response = self.client.post(reverse('supprimer_service', args=[9999]))
        self.assertEqual(response.status_code, 404)


class AdminPriseEnChargeFormTests(TestCase):
    def setUp(self):
        self.admin = creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')
        self.client.login(username='admin@santesn.sn', password=PASSWORD)
        self.patient = creer_patient()

    def test_creation_prise_en_charge_statut_en_attente_par_defaut(self):
        response = self.client.post(reverse('ajouter_prise_en_charge'), {
            'patient': self.patient.pk, 'motif': 'Consultation generale',
        })
        self.assertRedirects(response, reverse('liste_prises_en_charge'))
        prise = PriseEnCharge.objects.get(patient=self.patient)
        self.assertEqual(prise.statut, 'en_attente')

    def test_modification_statut_prise_en_charge(self):
        prise = PriseEnCharge.objects.create(patient=self.patient, motif='Test', statut='en_attente')
        response = self.client.post(reverse('modifier_prise_en_charge', args=[prise.pk]), {
            'patient': self.patient.pk, 'motif': 'Test modifie', 'statut': 'validee',
        })
        self.assertRedirects(response, reverse('liste_prises_en_charge'))
        prise.refresh_from_db()
        self.assertEqual(prise.statut, 'validee')
        self.assertEqual(prise.motif, 'Test modifie')

    def test_suppression_prise_en_charge(self):
        prise = PriseEnCharge.objects.create(patient=self.patient, motif='Test', statut='en_attente')
        response = self.client.post(reverse('supprimer_prise_en_charge', args=[prise.pk]))
        self.assertRedirects(response, reverse('liste_prises_en_charge'))
        self.assertFalse(PriseEnCharge.objects.filter(pk=prise.pk).exists())

    def test_suppression_prise_en_charge_inexistante_donne_404(self):
        response = self.client.post(reverse('supprimer_prise_en_charge', args=[9999]))
        self.assertEqual(response.status_code, 404)


class PaiementTests(TestCase):
    def setUp(self):
        self.medecin = creer_medecin('medecin@santesn.sn')
        self.patient = creer_patient()
        self.client.login(username='medecin@santesn.sn', password=PASSWORD)
        self.service = ServiceMedical.objects.create(nom='Consultation generale', prix=Decimal('10000'))

    def test_consultation_avec_prise_en_charge_validee_calcule_les_parts(self):
        plan = PlanCouverture.objects.create(nom='Standard', taux_couverture=Decimal('80.00'))
        self.patient.plan_couverture = plan
        self.patient.save()
        prise = PriseEnCharge.objects.create(patient=self.patient, motif='Test', statut='validee')

        self.client.post(reverse('ajouter_consultation_medecin'), {
            'patient': self.patient.pk,
            'service': self.service.pk,
            'prise_en_charge': prise.pk,
            'date_consultation': '2026-08-01T10:00',
            'diagnostic': 'Controle',
            'traitement': '',
        })
        paiement = Consultation.objects.get(patient=self.patient).paiement
        self.assertEqual(paiement.montant_total, Decimal('10000'))
        self.assertEqual(paiement.taux_applique, Decimal('80.00'))
        self.assertEqual(paiement.montant_part_assurance, Decimal('8000.00'))
        self.assertEqual(paiement.montant_part_patient, Decimal('2000.00'))
        self.assertEqual(paiement.statut, Paiement.Statut.NON_REGLE)

    def test_consultation_sans_prise_en_charge_validee_patient_paie_tout(self):
        prise_en_attente = PriseEnCharge.objects.create(patient=self.patient, motif='Test')
        self.client.post(reverse('ajouter_consultation_medecin'), {
            'patient': self.patient.pk,
            'service': self.service.pk,
            'prise_en_charge': prise_en_attente.pk,
            'date_consultation': '2026-08-01T10:00',
            'diagnostic': 'Controle',
            'traitement': '',
        })
        paiement = Consultation.objects.get(patient=self.patient).paiement
        self.assertEqual(paiement.montant_part_assurance, Decimal('0'))
        self.assertEqual(paiement.montant_part_patient, Decimal('10000'))

    def test_liste_paiements_interdite_aux_non_admins(self):
        response = self.client.get(reverse('liste_paiements'))
        self.assertEqual(response.status_code, 403)

    def test_liste_paiements_affiche_le_paiement_a_l_admin(self):
        self.client.logout()
        creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')
        self.client.login(username='admin@santesn.sn', password=PASSWORD)

        consultation = Consultation.objects.create(
            patient=self.patient, medecin=self.medecin, service=self.service,
            date_consultation=timezone.now(), diagnostic='Test',
        )
        Paiement.calculer_pour(consultation).save()

        response = self.client.get(reverse('liste_paiements'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Marquer regle')

    def test_marquer_paiement_regle(self):
        self.client.logout()
        creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')
        self.client.login(username='admin@santesn.sn', password=PASSWORD)

        consultation = Consultation.objects.create(
            patient=self.patient, medecin=self.medecin, service=self.service,
            date_consultation=timezone.now(), diagnostic='Test',
        )
        paiement = Paiement.calculer_pour(consultation)
        paiement.save()

        response = self.client.post(reverse('marquer_paiement_regle', args=[paiement.pk]), {
            'mode_reglement': 'ESPECES',
        })
        self.assertRedirects(response, reverse('liste_paiements'))
        paiement.refresh_from_db()
        self.assertEqual(paiement.statut, Paiement.Statut.REGLE)
        self.assertEqual(paiement.mode_reglement, 'ESPECES')
        self.assertIsNotNone(paiement.date_reglement)

    def test_marquer_paiement_regle_exige_mode_reglement(self):
        self.client.logout()
        creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')
        self.client.login(username='admin@santesn.sn', password=PASSWORD)

        consultation = Consultation.objects.create(
            patient=self.patient, medecin=self.medecin, service=self.service,
            date_consultation=timezone.now(), diagnostic='Test',
        )
        paiement = Paiement.calculer_pour(consultation)
        paiement.save()

        response = self.client.post(reverse('marquer_paiement_regle', args=[paiement.pk]), {
            'mode_reglement': '',
        })
        self.assertEqual(response.status_code, 200)
        paiement.refresh_from_db()
        self.assertEqual(paiement.statut, Paiement.Statut.NON_REGLE)


class PlanCouvertureAdminTests(TestCase):
    def setUp(self):
        self.admin = creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')
        self.client.login(username='admin@santesn.sn', password=PASSWORD)

    def test_liste_interdite_aux_non_admins(self):
        self.client.logout()
        creer_utilisateur(User.Role.MEDECIN, 'medecin@santesn.sn')
        self.client.login(username='medecin@santesn.sn', password=PASSWORD)
        response = self.client.get(reverse('liste_plans_couverture'))
        self.assertEqual(response.status_code, 403)

    def test_creation_modification_suppression_plan(self):
        response = self.client.post(reverse('ajouter_plan_couverture'), {
            'nom': 'Essentiel', 'taux_couverture': '70.00', 'plafond_annuel': '',
        })
        self.assertRedirects(response, reverse('liste_plans_couverture'))
        plan = PlanCouverture.objects.get(nom='Essentiel')

        response = self.client.post(reverse('modifier_plan_couverture', args=[plan.pk]), {
            'nom': 'Essentiel+', 'taux_couverture': '75.00', 'plafond_annuel': '',
        })
        self.assertRedirects(response, reverse('liste_plans_couverture'))
        plan.refresh_from_db()
        self.assertEqual(plan.nom, 'Essentiel+')

        response = self.client.post(reverse('supprimer_plan_couverture', args=[plan.pk]))
        self.assertRedirects(response, reverse('liste_plans_couverture'))
        self.assertFalse(PlanCouverture.objects.filter(pk=plan.pk).exists())


class SuppressionCascadeTests(TestCase):
    def setUp(self):
        self.admin = creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')
        self.client.login(username='admin@santesn.sn', password=PASSWORD)

    def test_avertissement_suppression_patient_avec_ayant_droit(self):
        patient = creer_patient()
        Patient.objects.create(
            nom='Diop', prenom='Petit', date_naissance=datetime.date(2015, 1, 1),
            type_beneficiaire=Patient.TypeBeneficiaire.AYANT_DROIT, assure_principal=patient,
        )
        response = self.client.get(reverse('supprimer_patient', args=[patient.pk]))
        self.assertContains(response, 'ayant(s) droit')

    def test_pas_davertissement_si_aucune_donnee_liee(self):
        patient = creer_patient()
        response = self.client.get(reverse('supprimer_patient', args=[patient.pk]))
        self.assertNotContains(response, 'Seront aussi supprimes')


class PharmacienSuppressionCompteTests(TestCase):
    def test_suppression_compte_pharmacien_preserve_la_fiche(self):
        admin = creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')
        pharmacien = creer_pharmacien('pharmacien@santesn.sn')
        utilisateur_pharmacien = pharmacien.user

        self.client.login(username='admin@santesn.sn', password=PASSWORD)
        response = self.client.post(reverse('supprimer_utilisateur', args=[utilisateur_pharmacien.pk]))
        self.assertRedirects(response, reverse('liste_utilisateurs'))

        pharmacien.refresh_from_db()
        self.assertIsNone(pharmacien.user)


class ValidationFormulairesTests(TestCase):
    def setUp(self):
        self.admin = creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')
        self.client.login(username='admin@santesn.sn', password=PASSWORD)

    def test_patient_ayant_droit_sans_principal_refuse(self):
        response = self.client.post(reverse('ajouter_patient'), {
            'nom': 'Diop', 'prenom': 'Fatou', 'date_naissance': '2015-01-01',
            'telephone': '', 'adresse': '',
            'type_beneficiaire': 'AYANT_DROIT', 'assure_principal': '', 'lien_parente': 'ENFANT',
            'plan_couverture': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Patient.objects.filter(nom='Diop', prenom='Fatou').exists())

    def test_patient_principal_avec_principal_refuse(self):
        autre_principal = creer_patient(nom='Sow', prenom='Awa')
        response = self.client.post(reverse('ajouter_patient'), {
            'nom': 'Diop', 'prenom': 'Fatou', 'date_naissance': '1990-01-01',
            'telephone': '', 'adresse': '',
            'type_beneficiaire': 'PRINCIPAL', 'assure_principal': autre_principal.pk,
            'lien_parente': '', 'plan_couverture': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Patient.objects.filter(nom='Diop', prenom='Fatou').exists())

    def test_telephone_invalide_refuse(self):
        response = self.client.post(reverse('ajouter_patient'), {
            'nom': 'Diop', 'prenom': 'Moussa', 'date_naissance': '1990-01-01',
            'telephone': 'pas-un-numero!!', 'adresse': '',
            'type_beneficiaire': 'PRINCIPAL', 'assure_principal': '', 'lien_parente': '',
            'plan_couverture': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Patient.objects.filter(nom='Diop', prenom='Moussa').exists())


class RendezVousDateValidationTests(TestCase):
    def setUp(self):
        self.medecin_utilisateur = creer_medecin('medecin@santesn.sn')
        self.patient = creer_patient()
        self.client.login(username='medecin@santesn.sn', password=PASSWORD)

    def test_rendez_vous_dans_le_passe_refuse(self):
        date_passee = (timezone.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        response = self.client.post(reverse('ajouter_rendez_vous'), {
            'patient': self.patient.pk, 'prestataire': '', 'date_heure': date_passee, 'motif': 'Test',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(RendezVous.objects.filter(patient=self.patient).exists())


class ConsultationPriseEnChargeValidationTests(TestCase):
    def setUp(self):
        self.medecin = creer_medecin('medecin@santesn.sn')
        self.patient = creer_patient()
        self.autre_patient = creer_patient(nom='Sow', prenom='Awa')
        self.client.login(username='medecin@santesn.sn', password=PASSWORD)

    def test_prise_en_charge_dun_autre_patient_refusee(self):
        prise_en_charge = PriseEnCharge.objects.create(patient=self.autre_patient, motif='Autre')
        response = self.client.post(reverse('ajouter_consultation_medecin'), {
            'patient': self.patient.pk, 'service': '', 'prise_en_charge': prise_en_charge.pk,
            'date_consultation': '2026-08-01T10:00', 'diagnostic': 'Test', 'traitement': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Consultation.objects.filter(patient=self.patient).exists())


class ChangerMotDePasseTests(TestCase):
    def setUp(self):
        self.utilisateur = creer_utilisateur(User.Role.ASSURE, 'assure@santesn.sn')

    def test_exige_connexion(self):
        response = self.client.get(reverse('changer_mot_de_passe'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_changement_reussi_reste_connecte(self):
        self.client.login(username='assure@santesn.sn', password=PASSWORD)
        nouveau_mot_de_passe = 'UnAutreMotDePasseSolide2026!'
        response = self.client.post(reverse('changer_mot_de_passe'), {
            'old_password': PASSWORD,
            'new_password1': nouveau_mot_de_passe,
            'new_password2': nouveau_mot_de_passe,
        })
        # Sans fiche Patient liee, post_login_redirect renchaine vers dashboard_assure
        # puis mon_profil_assure (302 en cascade) : sans rapport avec le mot de passe.
        self.assertRedirects(response, reverse('post_login_redirect'), target_status_code=302)

        # Toujours connecte (la session n'a pas ete invalidee par le changement).
        response = self.client.get(reverse('mon_profil_assure'))
        self.assertNotEqual(response.status_code, 302)

        self.utilisateur.refresh_from_db()
        self.assertTrue(self.utilisateur.check_password(nouveau_mot_de_passe))

    def test_ancien_mot_de_passe_incorrect_refuse(self):
        self.client.login(username='assure@santesn.sn', password=PASSWORD)
        response = self.client.post(reverse('changer_mot_de_passe'), {
            'old_password': 'mauvais',
            'new_password1': 'UnAutreMotDePasseSolide2026!',
            'new_password2': 'UnAutreMotDePasseSolide2026!',
        })
        self.assertEqual(response.status_code, 200)
        self.utilisateur.refresh_from_db()
        self.assertTrue(self.utilisateur.check_password(PASSWORD))

    def test_confirmation_differente_refusee(self):
        self.client.login(username='assure@santesn.sn', password=PASSWORD)
        response = self.client.post(reverse('changer_mot_de_passe'), {
            'old_password': PASSWORD,
            'new_password1': 'UnAutreMotDePasseSolide2026!',
            'new_password2': 'UnMotDePasseDifferent2026!',
        })
        self.assertEqual(response.status_code, 200)
        self.utilisateur.refresh_from_db()
        self.assertTrue(self.utilisateur.check_password(PASSWORD))


class ExportUtilisateursExcelTests(TestCase):
    def setUp(self):
        self.admin = creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')
        self.client.login(username='admin@santesn.sn', password=PASSWORD)

    def test_interdit_aux_non_admins(self):
        self.client.logout()
        creer_utilisateur(User.Role.MEDECIN, 'medecin@santesn.sn')
        self.client.login(username='medecin@santesn.sn', password=PASSWORD)
        response = self.client.get(reverse('exporter_utilisateurs_excel'))
        self.assertEqual(response.status_code, 403)

    def test_export_contient_le_bon_type_de_contenu_et_les_utilisateurs(self):
        creer_utilisateur(User.Role.MEDECIN, 'medecin1@santesn.sn')
        creer_utilisateur(User.Role.PHARMACIEN, 'pharmacien1@santesn.sn')

        response = self.client.get(reverse('exporter_utilisateurs_excel'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        self.assertIn('attachment', response['Content-Disposition'])

        classeur = openpyxl.load_workbook(io.BytesIO(response.content))
        feuille = classeur.active
        emails = [ligne[0].value for ligne in feuille.iter_rows(min_row=2)]
        self.assertIn('medecin1@santesn.sn', emails)
        self.assertIn('pharmacien1@santesn.sn', emails)
        self.assertIn('admin@santesn.sn', emails)

    def test_export_respecte_le_filtre_par_role(self):
        creer_utilisateur(User.Role.MEDECIN, 'medecin1@santesn.sn')
        creer_utilisateur(User.Role.PHARMACIEN, 'pharmacien1@santesn.sn')

        response = self.client.get(reverse('exporter_utilisateurs_excel'), {'role': 'MEDECIN'})
        classeur = openpyxl.load_workbook(io.BytesIO(response.content))
        feuille = classeur.active
        emails = [ligne[0].value for ligne in feuille.iter_rows(min_row=2)]
        self.assertIn('medecin1@santesn.sn', emails)
        self.assertNotIn('pharmacien1@santesn.sn', emails)


class ImportUtilisateursExcelTests(TestCase):
    def setUp(self):
        self.admin = creer_utilisateur(User.Role.ADMIN, 'admin@santesn.sn')
        self.client.login(username='admin@santesn.sn', password=PASSWORD)

    def test_page_interdite_aux_non_admins(self):
        self.client.logout()
        creer_utilisateur(User.Role.MEDECIN, 'medecin@santesn.sn')
        self.client.login(username='medecin@santesn.sn', password=PASSWORD)
        response = self.client.get(reverse('importer_utilisateurs_excel'))
        self.assertEqual(response.status_code, 403)

    def test_page_accessible_a_l_admin(self):
        response = self.client.get(reverse('importer_utilisateurs_excel'))
        self.assertEqual(response.status_code, 200)

    def test_modele_interdit_aux_non_admins(self):
        self.client.logout()
        creer_utilisateur(User.Role.MEDECIN, 'medecin@santesn.sn')
        self.client.login(username='medecin@santesn.sn', password=PASSWORD)
        response = self.client.get(reverse('telecharger_modele_import_utilisateurs'))
        self.assertEqual(response.status_code, 403)

    def test_modele_contient_les_bonnes_entetes(self):
        response = self.client.get(reverse('telecharger_modele_import_utilisateurs'))
        self.assertEqual(response.status_code, 200)
        classeur = openpyxl.load_workbook(io.BytesIO(response.content))
        entetes = [cellule.value for cellule in next(classeur.active.iter_rows(min_row=1, max_row=1))]
        self.assertEqual(entetes, ENTETES_IMPORT_UTILISATEURS)

    def test_import_multi_role_cree_les_comptes_et_fiches(self):
        prestataire = Prestataire.objects.create(nom='Hopital Test', type_prestataire='HOPITAL')
        plan = PlanCouverture.objects.create(nom='Standard', taux_couverture=Decimal('80.00'))
        fichier = creer_fichier_import_utilisateurs([
            ['fatou@ex.sn', 'Fatou', 'Ndiaye', '770000001', 'Assure', '15/03/1990', '', '', 'Standard'],
            ['jean@ex.sn', 'Jean', 'Diallo', '770000002', 'Medecin', '', 'Cardiologie', 'Hopital Test', ''],
            ['awa@ex.sn', 'Awa', 'Sow', '770000003', 'Pharmacien', '', '', '', ''],
        ])
        response = self.client.post(reverse('importer_utilisateurs_excel'), {'fichier': fichier})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'fatou@ex.sn')

        patient = Patient.objects.get(user__email='fatou@ex.sn')
        self.assertEqual(patient.type_beneficiaire, Patient.TypeBeneficiaire.PRINCIPAL)
        self.assertEqual(patient.plan_couverture, plan)

        medecin = Medecin.objects.get(email='jean@ex.sn')
        self.assertEqual(medecin.specialite, 'Cardiologie')
        self.assertEqual(medecin.prestataire, prestataire)

        pharmacien = Pharmacien.objects.get(user__email='awa@ex.sn')
        self.assertIsNotNone(pharmacien.user)

    def test_import_bloque_tout_si_une_ligne_est_invalide(self):
        fichier = creer_fichier_import_utilisateurs([
            ['valide@ex.sn', 'Valide', 'Test', '770000001', 'Pharmacien', '', '', '', ''],
            ['invalide@ex.sn', 'Invalide', 'Test', '770000002', 'RoleInconnu', '', '', '', ''],
        ])
        response = self.client.post(reverse('importer_utilisateurs_excel'), {'fichier': fichier})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='valide@ex.sn').exists())
        self.assertFalse(User.objects.filter(email='invalide@ex.sn').exists())

    def test_import_email_deja_existant_bloque_tout(self):
        creer_utilisateur(User.Role.MEDECIN, 'existant@ex.sn')
        fichier = creer_fichier_import_utilisateurs([
            ['nouveau@ex.sn', 'Nouveau', 'Test', '770000001', 'Pharmacien', '', '', '', ''],
            ['existant@ex.sn', 'Existant', 'Test', '770000002', 'Pharmacien', '', '', '', ''],
        ])
        response = self.client.post(reverse('importer_utilisateurs_excel'), {'fichier': fichier})
        self.assertFalse(User.objects.filter(email='nouveau@ex.sn').exists())

    def test_import_email_duplique_dans_le_fichier_bloque_tout(self):
        fichier = creer_fichier_import_utilisateurs([
            ['double@ex.sn', 'Un', 'Test', '770000001', 'Pharmacien', '', '', '', ''],
            ['double@ex.sn', 'Deux', 'Test', '770000002', 'Pharmacien', '', '', '', ''],
        ])
        response = self.client.post(reverse('importer_utilisateurs_excel'), {'fichier': fichier})
        self.assertEqual(User.objects.filter(email='double@ex.sn').count(), 0)

    def test_import_assure_sans_date_naissance_bloque_tout(self):
        fichier = creer_fichier_import_utilisateurs([
            ['sans.date@ex.sn', 'Sans', 'Date', '770000001', 'Assure', '', '', '', ''],
        ])
        response = self.client.post(reverse('importer_utilisateurs_excel'), {'fichier': fichier})
        self.assertFalse(User.objects.filter(email='sans.date@ex.sn').exists())

    def test_import_medecin_sans_telephone_bloque_tout(self):
        fichier = creer_fichier_import_utilisateurs([
            ['sans.tel@ex.sn', 'Sans', 'Tel', '', 'Medecin', '', 'Cardiologie', '', ''],
        ])
        response = self.client.post(reverse('importer_utilisateurs_excel'), {'fichier': fichier})
        self.assertFalse(User.objects.filter(email='sans.tel@ex.sn').exists())

    def test_import_entetes_invalides_est_refuse(self):
        fichier = creer_fichier_import_utilisateurs(
            [['x@ex.sn', 'X', 'Y', '770000001', 'Pharmacien', '', '', '', '']],
            entetes=['Colonne1', 'Colonne2'],
        )
        response = self.client.post(reverse('importer_utilisateurs_excel'), {'fichier': fichier})
        self.assertFalse(User.objects.filter(email='x@ex.sn').exists())
