from typing import Optional
from todo_app.mcp import mcp
import frappe
import json


@mcp.tool()
def get_stock_balance(item_code: str, warehouse: Optional[str] = None):
    """Get current stock balance for an item.

    Args:
        item_code: The item code
        warehouse: Optional specific warehouse (returns all if not specified)
    """

    from erpnext.stock.utils import get_stock_balance as erp_get_stock_balance

    # TODO: calling user must have Stock User role
    try:
        if warehouse:
            balance = erp_get_stock_balance(item_code, warehouse)
            return {"item_code": item_code, "warehouse": warehouse, "balance": balance}

        else:
            warehouses = frappe.get_all("Warehouse", pluck="name")
            balances = []

            for wh in warehouses:
                balance = erp_get_stock_balance(item_code, wh)
                if balance and balance > 0:
                    balances.append({"warehouse": wh, "balance": balance})

            return {
                "item_code": item_code,
                "total_warehouses": len(balances),
                "balances": balances,
            }

    except Exception:
        return {"success": False, "error": frappe.get_traceback()}


@mcp.tool()
def get_low_stock_items(threshold: int = 10):
    """Get items with stock below threshold.

    Args:
        threshold: Minimum stock quantity threshold
    """
    low_stock = frappe.db.sql(
        """
        SELECT item_code, warehouse, actual_qty
        FROM `tabBin`
        WHERE actual_qty < %s
        ORDER BY actual_qty ASC
        LIMIT 50
    """,
        (threshold,),
        as_dict=True,
    )

    return json.loads(
        json.dumps(
            {"threshold": threshold, "count": len(low_stock), "items": low_stock},
            default=str,
        )
    )
