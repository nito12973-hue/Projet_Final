def user_role(request):
    """Expose le rôle de l'utilisateur connecté à tous les templates."""
    user = getattr(request, 'user', None)
    if user is not None and user.is_authenticated:
        return {
            'current_role': user.role,
            'current_role_label': user.get_role_display(),
        }
    return {'current_role': None, 'current_role_label': None}
