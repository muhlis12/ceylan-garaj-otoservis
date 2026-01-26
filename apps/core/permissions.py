from __future__ import annotations

from functools import wraps
from typing import Iterable, Optional

from django.contrib import messages
from django.shortcuts import redirect

from apps.core.models import BranchMembership


def get_active_branch_id(request) -> Optional[int]:
    bid = request.session.get("active_branch_id")
    return int(bid) if bid else None


def get_active_role(request) -> Optional[str]:
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return None
    bid = get_active_branch_id(request)
    if not bid:
        return None
    bm = BranchMembership.objects.filter(user=request.user, branch_id=bid, is_active=True).first()
    return bm.role if bm else None


def role_required(roles: Iterable[str]):
    roles_set = set(roles)

    def deco(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            role = get_active_role(request)
            if role not in roles_set:
                messages.error(request, "Bu işlem için yetkin yok.")
                return redirect("/")
            return view_func(request, *args, **kwargs)

        return _wrapped

    return deco
