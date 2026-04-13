# # inventory_app/inventory_app/tools/item_tools.py
# from todo_app.mcp import mcp
# import frappe

# @mcp.tool()
# def search_items(search_term: str, item_group: str = None):
#     """Search for items by name or code.
    
#     Args:
#         search_term: Text to search in item name or code
#         item_group: Optional filter by item group
#     """
#     filters = {"item_name": ["like", f"%{search_term}%"]}
    
#     if item_group:
#         filters["item_group"] = item_group
    
#     items = frappe.get_all(
#         "Item",
#         filters=filters,
#         fields=["name", "item_name", "item_group", "stock_uom"],
#         limit=20
#     )
    
#     return {
#         "items": items,
#         "count": len(items)
#     }

# @mcp.tool()
# def get_item_details(item_code: str):
#     """Get detailed information about a specific item.
    
#     Args:
#         item_code: The item code to look up
#     """
#     if not frappe.db.exists("Item", item_code):
#         return {"error": f"Item {item_code} not found"}
    
#     item = frappe.get_doc("Item", item_code)
    
#     return {
#         "item_code": item.name,
#         "item_name": item.item_name,
#         "description": item.description,
#         "item_group": item.item_group,
#         "stock_uom": item.stock_uom,
#         "standard_rate": item.standard_rate,
#         "is_stock_item": item.is_stock_item
#     }

# @mcp.tool()
# def create_item(item_name: str, item_group: str, stock_uom: str = "Nos"):
#     """Create a new item in the system.
    
#     Args:
#         item_name: Name of the item
#         item_group: Item group classification
#         stock_uom: Unit of measurement (default: Nos)
#     """
#     try:
#         item = frappe.get_doc({
#             "doctype": "Item",
#             "item_name": item_name,
#             "item_group": item_group,
#             "stock_uom": stock_uom,
#             "is_stock_item": 1
#         })
#         item.insert()
#         frappe.db.commit()
        
#         return {
#             "success": True,
#             "item_code": item.name,
#             "message": f"Item {item.name} created successfully"
#         }
#     except Exception as e:
#         return {
#             "success": False,
#             "error": str(e)
#         }