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
from django.conf import settings
from django.contrib import admin
from django.http import Http404, HttpResponse
from django.urls import path, include, re_path
from django.views.static import serve


def servir_fichier_media(request, path):
    """Sert les fichiers médias depuis la base de données (FichierMedia) ou le disque en secours."""
    path_propre = path.replace("\\", "/").lstrip("/")

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
            return response
    except Exception:
        pass

    # 2. Secours sur le disque local
    try:
        return serve(request, path, document_root=settings.MEDIA_ROOT)
    except Http404:
        raise Http404(f"« {path} » n'existe pas.")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('Plateform_medicale.urls')),
    re_path(r'^media/(?P<path>.*)$', servir_fichier_media, name='media_serve'),
]


