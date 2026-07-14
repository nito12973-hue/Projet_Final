from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """
    Restreint une vue aux rôles indiqués.

    Exemple :
        @role_required(User.Role.ADMIN, User.Role.MEDECIN)
        def ma_vue(request): ...
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def admin_required(view_func):
    """Restreint une vue au rôle ADMIN uniquement."""
    from .models import User

    return role_required(User.Role.ADMIN)(view_func)
