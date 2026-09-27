import mimetypes
import os
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class DatabaseMediaStorage(Storage):
    """Storage hybride base de données + disque.
    - Écrit et lit prioritairement dans FichierMedia (persistance PostgreSQL sur Vercel serverless).
    - Sauvegarde également sur disque local en développement ou en cache si le système de fichiers est accessible en écriture.
    - Résilient aux systèmes de fichiers en lecture seule (comme AWS Lambda / Vercel /var/task).
    """

    def _get_model(self):
        from .models import FichierMedia
        return FichierMedia

    def _save(self, name, content):
        name = name.replace("\\", "/").lstrip("/")
        content.seek(0)
        donnees = content.read()
        type_mime, _ = mimetypes.guess_type(name)
        if not type_mime:
            type_mime = "application/octet-stream"

        FichierMedia = self._get_model()
        FichierMedia.objects.update_or_create(
            chemin=name,
            defaults={
                "contenu": donnees,
                "type_mime": type_mime,
                "taille": len(donnees),
            },
        )

        # Tentative de sauvegarde miroir sur disque si possible
        try:
            chemin_disque = os.path.join(settings.MEDIA_ROOT, name)
            dossier = os.path.dirname(chemin_disque)
            os.makedirs(dossier, exist_ok=True)
            with open(chemin_disque, "wb") as f:
                f.write(donnees)
        except OSError:
            pass

        return name

    def _open(self, name, mode="rb"):
        name = name.replace("\\", "/").lstrip("/")
        FichierMedia = self._get_model()
        media = FichierMedia.objects.filter(chemin=name).first()
        if media:
            return ContentFile(media.contenu, name=name)

        chemin_disque = os.path.join(settings.MEDIA_ROOT, name)
        if os.path.exists(chemin_disque):
            with open(chemin_disque, mode) as f:
                return ContentFile(f.read(), name=name)

        raise FileNotFoundError(f"Le fichier média {name} est introuvable.")

    def exists(self, name):
        name = name.replace("\\", "/").lstrip("/")
        FichierMedia = self._get_model()
        if FichierMedia.objects.filter(chemin=name).exists():
            return True
        chemin_disque = os.path.join(settings.MEDIA_ROOT, name)
        return os.path.exists(chemin_disque)

    def size(self, name):
        name = name.replace("\\", "/").lstrip("/")
        FichierMedia = self._get_model()
        media = FichierMedia.objects.filter(chemin=name).first()
        if media:
            return media.taille
        chemin_disque = os.path.join(settings.MEDIA_ROOT, name)
        if os.path.exists(chemin_disque):
            return os.path.getsize(chemin_disque)
        return 0

    def url(self, name):
        name = name.replace("\\", "/").lstrip("/")
        return f"{settings.MEDIA_URL}{name}"

    def delete(self, name):
        name = name.replace("\\", "/").lstrip("/")
        FichierMedia = self._get_model()
        FichierMedia.objects.filter(chemin=name).delete()
        try:
            chemin_disque = os.path.join(settings.MEDIA_ROOT, name)
            if os.path.exists(chemin_disque):
                os.remove(chemin_disque)
        except OSError:
            pass
