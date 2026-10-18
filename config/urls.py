"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os
import posixpath
from django.conf import settings
from django.contrib import admin
from django.http import Http404, HttpResponse
from django.urls import path, include, re_path
from django.views.static import serve


DOSSIERS_MEDIAS_SENSIBLES = (
    "justificatifs_remboursements",
    "documents_patients",
    "documents_ayants_droit",
    "justificatifs_ayants_droit",
    "devis_prises_en_charge",
    "ordonnances",
)


def servir_fichier_media(request, path):
    """
    Sert les fichiers médias publics ou protégés.
    RÈGLE DE SÉCURITÉ MÉDICALE :
    Les documents confidentiels (justificatifs, pièces d'identité, devis) ne peuvent JAMAIS
    être servis par cette route générique non authentifiée. Ils doivent transiter par
    les contrôleurs sécurisés avec vérification multi-organismes.
    """
    path_norm = posixpath.normpath(path.replace("\\", "/")).lstrip("/")
    if path_norm.startswith("../") or "/../" in path_norm or path_norm == "..":
        raise Http404("Chemin de fichier média non autorisé.")

    path_propre = path_norm

    # Interdiction formelle d'accès direct aux pièces sensibles
    for dossier in DOSSIERS_MEDIAS_SENSIBLES:
        if path_propre.startswith(f"{dossier}/") or path_propre == dossier:
            raise Http404("Accès interdit : ce document médical confidentiel nécessite une authentification dédiée.")

    # 1. Base de données PostgreSQL (FichierMedia) : persistance serverless Vercel
    try:
        from Plateform_medicale.models import FichierMedia
        media = FichierMedia.objects.filter(chemin=path_propre).first()
        if media:
            response = HttpResponse(media.contenu, content_type=media.type_mime)
            nom_fichier = os.path.basename(path_propre)
            response["Content-Disposition"] = f'inline; filename="{nom_fichier}"'
            response["Content-Length"] = str(media.taille)
            response["Cache-Control"] = "public, max-age=86400"
            response["X-Content-Type-Options"] = "nosniff"
            return response
    except Exception:
        pass

    # 2. Secours sur le disque local pour les médias non sensibles (logos, illustrations)
    try:
        response = serve(request, path, document_root=settings.MEDIA_ROOT)
        response["X-Content-Type-Options"] = "nosniff"
        return response
    except Http404:
        raise Http404(f"« {path} » n'existe pas.")


from Plateform_medicale import views as plateform_views

urlpatterns = [
    path('admin/logs', plateform_views.journal_activite, name='admin_logs_sans_slash'),
    path('admin/logs/', plateform_views.journal_activite, name='admin_logs'),
    path('admin/', admin.site.urls),
    path('', include('Plateform_medicale.urls')),
    re_path(r'^media/(?P<path>.*)$', servir_fichier_media, name='media_serve'),
]


