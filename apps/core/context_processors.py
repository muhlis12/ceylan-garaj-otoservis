from apps.core.models import Branch, BranchMembership



def active_branch(request):
    """Provide active branch + role for templates."""
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {
            "active_branch": None,
            "active_branch_id": None,
            "active_role": None,
            "can_manage": False,
            "can_work": False,
        }

    bid = request.session.get("active_branch_id")

    # Auto-pick first membership if missing
    if not bid:
        bm = BranchMembership.objects.filter(user=request.user, is_active=True).select_related("branch").first()
        if bm:
            request.session["active_branch_id"] = bm.branch_id
            bid = bm.branch_id

    branch = Branch.objects.filter(id=bid).first() if bid else None

    role = None
    if bid:
        bm2 = BranchMembership.objects.filter(user=request.user, branch_id=bid, is_active=True).first()
        role = bm2.role if bm2 else None

    can_manage = role in (BranchMembership.ROLE_ADMIN, BranchMembership.ROLE_MANAGER)
    can_work = role in (BranchMembership.ROLE_ADMIN, BranchMembership.ROLE_MANAGER, BranchMembership.ROLE_TECH, BranchMembership.ROLE_WASH)

    return {
        "active_branch": branch,
        "active_branch_id": bid,
        "active_role": role,
        "can_manage": can_manage,
        "can_work": can_work,
    }
