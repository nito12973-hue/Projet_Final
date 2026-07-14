from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modèle utilisateur unique de SantéSN.

    Règles métier :
    - authentification par email + mot de passe uniquement
    - le rôle est stocké en base et jamais choisi à la connexion
    - la redirection après connexion dépend du rôle
    """

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrateur'
        ASSURE = 'ASSURE', 'Assuré'
        MEDECIN = 'MEDECIN', 'Médecin'
        PHARMACIEN = 'PHARMACIEN', 'Pharmacien'

    email = models.EmailField('adresse email', unique=True)
    first_name = models.CharField('prénom', max_length=150, blank=True)
    last_name = models.CharField('nom', max_length=150, blank=True)
    phone_number = models.CharField('téléphone', max_length=20, blank=True)
    role = models.CharField(
        'rôle',
        max_length=20,
        choices=Role.choices,
        db_index=True,
    )

    is_staff = models.BooleanField('accès au back-office', default=False)
    is_active = models.BooleanField('compte actif', default=True)
    date_joined = models.DateTimeField('date de création', default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'utilisateur'
        verbose_name_plural = 'utilisateurs'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        full_name = self.get_full_name()
        return f'{full_name} ({self.email})' if full_name else self.email

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    def get_short_name(self):
        return self.first_name

    # Aides métier utilisées par les décorateurs et les templates
    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    @property
    def is_assure(self):
        return self.role == self.Role.ASSURE

    @property
    def is_medecin(self):
        return self.role == self.Role.MEDECIN

    @property
    def is_pharmacien(self):
        return self.role == self.Role.PHARMACIEN
