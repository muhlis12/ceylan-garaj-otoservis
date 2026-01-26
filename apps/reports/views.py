from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, DecimalField, F, ExpressionWrapper, Q
from django.db.models.functions import Coalesce, TruncDate
from django.shortcuts import redirect, render

from apps.core.models import BranchMembership
from apps.workorders.models import WorkOrder


def _can_manage(request, branch_id: int) -> bool:
    role = (
        BranchMembership.objects
        .filter(user=request.user, branch_id=branch_id, is_active=True)
        .values_list("role", flat=True)
        .first()
    )
    return role in (BranchMembership.ROLE_ADMIN, BranchMembership.ROLE_MANAGER)


def _get_date_range(request):
    """GET paramlarından tarih aralığını alır (default son 30 gün)."""
    try:
        start_str = request.GET.get("start")
        end_str = request.GET.get("end")
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date() if start_str else (datetime.now() - timedelta(days=30)).date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date() if end_str else datetime.now().date()
    except Exception:
        start_date = (datetime.now() - timedelta(days=30)).date()
        end_date = datetime.now().date()
    return start_date, end_date


@login_required
def revenue_report(request):
    """
    ✅ Gelir raporu: DONE iş emirleri
    ✅ Tarih baz alınan alan: finished_at (iş bittiği gün)
    """
    branch_id = request.session.get("active_branch_id")
    if not branch_id:
        messages.error(request, "Aktif şube seçili değil.")
        return redirect("/")

    if not _can_manage(request, int(branch_id)):
        messages.error(request, "Bu sayfa için yetkin yok.")
        return redirect("/")

    start_date, end_date = _get_date_range(request)

    DEC0 = Decimal("0.00")
    DECIMAL = DecimalField(max_digits=12, decimal_places=2)

    qs = (
        WorkOrder.objects
        .filter(branch_id=branch_id, status=WorkOrder.STATUS_DONE)
        .filter(finished_at__isnull=False)  # ✅ bitiş tarihi yoksa rapora girme
        .filter(finished_at__date__gte=start_date, finished_at__date__lte=end_date)
    )

    daily_qs = (
        qs.annotate(day=TruncDate("finished_at"))  # ✅ created_at değil!
        .values("day")
        .annotate(
            count=Count("id"),
            sum_grand=Coalesce(Sum("grand_total"), DEC0, output_field=DECIMAL),
            sum_labor=Coalesce(Sum("labor_total"), DEC0, output_field=DECIMAL),
            sum_parts=Coalesce(Sum("parts_total"), DEC0, output_field=DECIMAL),
        )
        .order_by("day")
    )

    rows = list(daily_qs)

    totals = qs.aggregate(
        labor_total=Coalesce(Sum("labor_total"), DEC0, output_field=DECIMAL),
        parts_total=Coalesce(Sum("parts_total"), DEC0, output_field=DECIMAL),
        grand_total=Coalesce(Sum("grand_total"), DEC0, output_field=DECIMAL),
    )

    chart_labels = [r["day"].strftime("%d.%m") for r in rows]
    chart_grand = [float(r["sum_grand"] or 0) for r in rows]
    chart_labor = [float(r["sum_labor"] or 0) for r in rows]
    chart_parts = [float(r["sum_parts"] or 0) for r in rows]

    return render(
        request,
        "reports/revenue_report.html",
        {
            "rows": rows,
            "totals": totals,
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "chart_labels": chart_labels,
            "chart_grand": chart_grand,
            "chart_labor": chart_labor,
            "chart_parts": chart_parts,
        },
    )


@login_required
def profit_report(request):
    """
    ✅ Karlılık raporu: profit = grand_total - parça maliyeti
    ✅ Tarih baz alınan alan: finished_at (iş bittiği gün)
    """
    branch_id = request.session.get("active_branch_id")
    if not branch_id:
        messages.error(request, "Aktif şube seçili değil.")
        return redirect("/")

    if not _can_manage(request, int(branch_id)):
        messages.error(request, "Bu sayfa için yetkin yok.")
        return redirect("/")

    start_date, end_date = _get_date_range(request)

    DEC0 = Decimal("0.00")
    DECIMAL = DecimalField(max_digits=12, decimal_places=2)

    # WorkOrder.parts -> WorkOrderPart.qty and WorkOrderPart.part.cost_price
    part_cost_expr = ExpressionWrapper(
        F("parts__qty") * F("parts__part__cost_price"),
        output_field=DECIMAL,
    )

    qs = (
        WorkOrder.objects
        .filter(branch_id=branch_id, status=WorkOrder.STATUS_DONE)
        .filter(finished_at__isnull=False)
        .filter(finished_at__date__gte=start_date, finished_at__date__lte=end_date)
    )

    daily = (
        qs.annotate(day=TruncDate("finished_at"))  # ✅ created_at değil!
        .values("day")
        .annotate(
            count=Count("id"),
            revenue=Coalesce(Sum("grand_total"), DEC0, output_field=DECIMAL),
            parts_cost=Coalesce(Sum(part_cost_expr), DEC0, output_field=DECIMAL),
        )
        .order_by("day")
    )

    rows = list(daily)
    for r in rows:
        r["profit"] = (r["revenue"] or DEC0) - (r["parts_cost"] or DEC0)

    totals = {
        "revenue": sum((r["revenue"] for r in rows), DEC0),
        "parts_cost": sum((r["parts_cost"] for r in rows), DEC0),
        "profit": sum((r["profit"] for r in rows), DEC0),
    }

    chart_labels = [r["day"].strftime("%d.%m") for r in rows]
    chart_revenue = [float(r["revenue"] or 0) for r in rows]
    chart_cost = [float(r["parts_cost"] or 0) for r in rows]
    chart_profit = [float(r["profit"] or 0) for r in rows]

    return render(
        request,
        "reports/profit_report.html",
        {
            "rows": rows,
            "totals": totals,
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "chart_labels": chart_labels,
            "chart_revenue": chart_revenue,
            "chart_cost": chart_cost,
            "chart_profit": chart_profit,
        },
    )
