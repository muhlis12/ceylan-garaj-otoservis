from decimal import Decimal
from django.db.models import Sum, DecimalField
from django.db.models.functions import Coalesce
from .models import StockMove

DECIMAL = DecimalField(max_digits=12, decimal_places=2)
DEC0 = Decimal("0.00")

def get_stock(branch_id: int, part_id: int) -> Decimal:
    qs = StockMove.objects.filter(branch_id=branch_id, part_id=part_id)
    in_sum = qs.filter(move_type=StockMove.TYPE_IN).aggregate(v=Coalesce(Sum("qty"), DEC0, output_field=DECIMAL))["v"]
    out_sum = qs.filter(move_type=StockMove.TYPE_OUT).aggregate(v=Coalesce(Sum("qty"), DEC0, output_field=DECIMAL))["v"]
    return (in_sum or DEC0) - (out_sum or DEC0)
