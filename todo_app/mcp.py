import frappe
import frappe_mcp
from frappe_mcp import Tool, ToolAnnotations

mcp = frappe_mcp.MCP("mcp")

@mcp.tool()
def get_todos(status: str = "Open"):
    """Fetch all TODO items with the specified status.

    Args:
        status: Filter by status (Open, Closed, or All)
    """
    import frappe
    
    if status == "All":
        todos = frappe.get_all("ToDo", fields=["name", "description", "status"])
    else:
        todos = frappe.get_all(
            "ToDo",
            filters={"status": status},
            fields=["name", "description", "status"]
        )

    cleaned = []
    for t in todos:
        cleaned.append({
            "name": str(t.get("name") or ""),
            "description": str(t.get("description") or ""),
            "status": str(t.get("status") or "")
        })

    return {
        "todos": cleaned,
        "count": int(len(cleaned))
    }
@mcp.tool()
def create_todo(description: str, priority: str = "Medium"):
    """Create a new TODO item.
    
    Args:
        description: The TODO description
        priority: Priority level (Low, Medium, High)
    """
    import frappe
    
    todo = frappe.get_doc({
        "doctype": "ToDo",
        "description": description,
        "priority": priority,
        "status": "Open"
    })
    todo.insert()
    
    return {"success": True, "todo_id": todo.name}

@mcp.tool()
def mark_done(todo_id: str):
    """Mark a TODO item as completed.
    
    Args:
        todo_id: The ID of the TODO item to complete
    """
    import frappe
    
    todo = frappe.get_doc("ToDo", todo_id)
    todo.status = "Closed"
    todo.save()
    
    return {"success": True, "message": f"TODO {todo_id} marked as done"}

# --- Tutorial examples ---

@mcp.tool()
def simple_tool(param1 : str):
    return {"result":param1}

@mcp.tool(name="custom_name")
def param_tool(param: str):
    return {"result": param}

# --- Using mcp.add_tool() ---

def calculate_tax(amount: float, tax_rate: float):
    """Calculate tax on an amount."""
    return {"tax": amount * tax_rate, "total": amount * (1 + tax_rate)}


tax_tool = Tool(
    name="calculate_tax",
    description="Calculate tax and total amount",
    input_schema={
        "type": "object",
        "properties": {
            "amount": {"type": "number", "description": "Base amount"},
            "tax_rate": {"type": "number", "description": "Tax rate (e.g., 0.18 for 18%)"}
        },
        "required": ["amount", "tax_rate"]
    },
    output_schema=None,
    annotations=ToolAnnotations(readOnlyHint=True),
    fn=calculate_tax
)

mcp.add_tool(tax_tool)

# --- App tools ---
# Using frappe.whitelist directly instead of mcp.register() to avoid a bug
# where mcp.register()'s inner wrapper loses __module__, causing Frappe v17
# to fail when resolving the app name for type validation.
@frappe.whitelist(allow_guest=True)  # TODO: replace with OAuth once configured
def handle_mcp():
    import todo_app.tools.item_tools
    import todo_app.tools.stock_tools
    import todo_app.tools.customers
    return mcp.handle(frappe.request, frappe.response)