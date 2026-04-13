
# from todo_app.mcp import mcp
# import frappe

# @mcp.tool()
# def get_stock_balance(item_code: str, warehouse: str = None):
#     """Get current stock balance for an item.
    
#     Args:
#         item_code: The item code
#         warehouse: Optional specific warehouse (returns all if not specified)
#     """
#     from erpnext.stock.utils import get_stock_balance
    
#     if warehouse:
#         balance = get_stock_balance(item_code, warehouse)
#         return {
#             "item_code": item_code,
#             "warehouse": warehouse,
#             "balance": balance
#         }
#     else:
#         warehouses = frappe.get_all("Warehouse", fields=["name"])
#         balances = []
        
#         for wh in warehouses:
#             balance = get_stock_balance(item_code, wh.name)
#             if balance > 0:
#                 balances.append({
#                     "warehouse": wh.name,
#                     "balance": balance
#                 })
        
#         return {
#             "item_code": item_code,
#             "total_warehouses": len(balances),
#             "balances": balances
#         }

# @mcp.tool()
# def get_low_stock_items(threshold: int = 10):
#     """Get items with stock below threshold.
    
#     Args:
#         threshold: Minimum stock quantity threshold
#     """
#     low_stock = frappe.db.sql("""
#         SELECT item_code, warehouse, actual_qty
#         FROM `tabBin`
#         WHERE actual_qty < %s
#         ORDER BY actual_qty ASC
#         LIMIT 50
#     """, (threshold,), as_dict=True)
    
#     return {
#         "threshold": threshold,
#         "count": len(low_stock),
#         "items": low_stock
#     }