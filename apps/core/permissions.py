from django.contrib import messages
from django.shortcuts import redirect
from functools import wraps
from apps.core.models import BranchMembership

def _active_role(request):
    bid = request.session.get("active_branch_id")
    qs = BranchMembership.objects.filter(user=request.user, is_active=True)
    if bid:
        qs = qs.filter(branch_id=bid)
    bm = qs.first()
    return bm.role if bm else None

def is_admin_request(request) -> bool:
    role = _active_role(request)
    return role in (BranchMembership.ROLE_ADMIN, BranchMembership.ROLE_MANAGER)

def is_worker_request(request) -> bool:
    role = _active_role(request)
    return role in (BranchMembership.ROLE_TECH, BranchMembership.ROLE_WASH)

def admin_required(view):
    @wraps(view)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("/accounts/login/")
        if not is_admin_request(request):
            messages.error(request, "Bu alan sadece admin içindir.")
            return redirect("/workorders/my/")
        return view(request, *args, **kwargs)
    return _wrapped

def worker_required(view):
    @wraps(view)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("/accounts/login/")
        if not is_worker_request(request):
            messages.error(request, "Bu alan sadece usta içindir.")
            return redirect("/workorders/")
        return view(request, *args, **kwargs)
    return _wrapped
