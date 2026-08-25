"""Notifications : envoi (admin), liste envoyées, mes notifications, marquer lue."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from ..forms import EnvoyerNotificationForm
from ..models import Notification, User
from .utils import _paginer, admin_required


@admin_required
def envoyer_notification(request):
    if request.method == "POST":
        form = EnvoyerNotificationForm(request.POST)
        if form.is_valid():
            message = form.cleaned_data["message"]
            destinataire = form.cleaned_data["destinataire"]
            role = form.cleaned_data["role"]

            if destinataire:
                destinataires = [destinataire]
            else:
                destinataires = list(User.objects.filter(role=role, is_active=True))

            Notification.objects.bulk_create(
                [Notification(destinataire=u, message=message) for u in destinataires]
            )
            messages.success(request, f"Notification envoyée à {len(destinataires)} utilisateur(s).")
            return redirect("liste_notifications_envoyees")
    else:
        form = EnvoyerNotificationForm()
    return render(request, "envoyer_notification.html", {"form": form})


@admin_required
def liste_notifications_envoyees(request):
    notifications = Notification.objects.select_related("destinataire").all()

    lue = request.GET.get("lue", "")
    if lue == "oui":
        notifications = notifications.filter(lue=True)
    elif lue == "non":
        notifications = notifications.filter(lue=False)

    recherche = request.GET.get("q", "").strip()
    if recherche:
        notifications = notifications.filter(
            Q(message__icontains=recherche)
            | Q(destinataire__email__icontains=recherche)
            | Q(destinataire__first_name__icontains=recherche)
            | Q(destinataire__last_name__icontains=recherche)
        )

    # Le plafond des 200 plus recentes s'applique une fois les filtres
    # appliques (sinon une recherche pourrait manquer une notification plus
    # ancienne que les 200 dernieres notifications tous destinataires confondus).
    notifications = notifications[:200]

    contexte = {
        "notifications": _paginer(request, notifications),
        "lue_choisie": lue,
        "recherche": recherche,
    }
    return render(request, "liste_notifications_envoyees.html", contexte)


@login_required
def mes_notifications(request):
    notifications = request.user.notifications.all()

    lue = request.GET.get("lue", "")
    if lue == "oui":
        notifications = notifications.filter(lue=True)
    elif lue == "non":
        notifications = notifications.filter(lue=False)

    contexte = {
        "notifications": _paginer(request, notifications),
        "lue_choisie": lue,
    }
    return render(request, "mes_notifications.html", contexte)


@login_required
@require_POST
def marquer_notification_lue(request, pk):
    notification = get_object_or_404(Notification, pk=pk, destinataire=request.user)
    notification.lue = True
    notification.save(update_fields=["lue"])
    next_url = request.POST.get("next") or reverse("mes_notifications")
    return redirect(next_url)


@login_required
@require_POST
def marquer_toutes_notifications_lues(request):
    request.user.notifications.filter(lue=False).update(lue=True)
    messages.success(request, "Toutes vos notifications ont été marquées comme lues.")
    next_url = request.POST.get("next") or reverse("mes_notifications")
    return redirect(next_url)


@login_required
def api_dernieres_notifications(request):
    from django.http import JsonResponse
    notifications = request.user.notifications.all()[:5]
    non_lues = request.user.notifications.filter(lue=False).count()
    data = {
        "non_lues_count": non_lues,
        "notifications": [
            {
                "id": n.pk,
                "titre": n.titre,
                "message": n.message,
                "type": n.get_type_evenement_display(),
                "lue": n.lue,
                "date": n.date_creation.strftime("%d/%m/%Y à %H:%M"),
                "url_action": n.url_action or reverse("mes_notifications"),
            }
            for n in notifications
        ],
    }
    return JsonResponse(data)
