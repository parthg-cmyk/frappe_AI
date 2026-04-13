# Frappe MCP Tutorial: Complete Guide

A comprehensive guide to building Model Context Protocol (MCP) servers with Frappe Framework.

## Table of Contents

1. [Introduction](#introduction)
2. [What is Frappe MCP?](#what-is-frappe-mcp)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Quick Start](#quick-start)
6. [Core Concepts](#core-concepts)
7. [Building Your First MCP Server](#building-your-first-mcp-server)
8. [Working with Tools](#working-with-tools)
9. [Authentication Setup](#authentication-setup)
10. [Testing and Debugging](#testing-and-debugging)
11. [Advanced Topics](#advanced-topics)
12. [Best Practices](#best-practices)
13. [Troubleshooting](#troubleshooting)

---

## Introduction

Frappe MCP enables your Frappe Framework applications to function as MCP (Model Context Protocol) servers, allowing Large Language Models (LLMs) to interact with your Frappe apps through standardized tools and APIs.

### What is MCP?

Model Context Protocol (MCP) is a standard protocol that allows LLMs to interact with external tools and data sources in a secure, controlled manner. It uses JSON-RPC for communication and supports:

- **Tools**: Functions that LLMs can call
- **Resources**: Data sources that LLMs can access
- **Prompts**: Reusable prompt templates

### Why Frappe MCP?

The official Python MCP SDK only supports async (ASGI) servers, but Frappe Framework uses Werkzeug (WSGI). Frappe MCP provides a from-scratch implementation designed specifically for Frappe's synchronous architecture.

---

## What is Frappe MCP?

Frappe MCP is a Python library that:

- Turns your Frappe app into a Streamable HTTP MCP server
- Handles JSON-RPC request/response formatting
- Manages tool registration and execution
- Integrates seamlessly with Frappe's authentication system
- Works with Werkzeug/WSGI servers

**Current Status**: Experimental - supports Tools only. Resources, prompts, and SSE streaming coming soon.

---

## Prerequisites

Before starting, ensure you have:

1. **Frappe Framework** installed (version with OAuth2 support recommended)
2. **Python 3.8+**
3. **Basic understanding of**:
   - Frappe Framework
   - Python decorators
   - REST APIs
   - JSON Schema (helpful but not required)

---

## Installation

### Using pip

```bash
pip install frappe-mcp
```

### Using uv (recommended)

```bash
uv add frappe-mcp
```

### Verify Installation

After installation, activate your Frappe bench environment and run:

```bash
source ./env/bin/activate
frappe-mcp --version
```

---

## Quick Start

Let's build a simple TODO MCP server in 5 minutes.

### Step 1: Create MCP Instance

Create a new file `mcp.py` in your app directory (same level as `hooks.py`):

```python
# todo_app/todo_app/mcp.py
import frappe_mcp

# Create MCP instance with a unique name
mcp = frappe_mcp.MCP("todo-mcp")
```

### Step 2: Register Tools

Add tools to your MCP server:

```python
# todo_app/todo_app/mcp.py
import frappe_mcp

mcp = frappe_mcp.MCP("todo-mcp")

@mcp.tool()
def get_todos(status: str = "Open"):
    """Fetch all TODO items with the specified status.
    
    Args:
        status: Filter by status (Open, Completed, or All)
    """
    import frappe
    
    if status == "All":
        todos = frappe.get_all("ToDo", fields=["name", "description", "status"])
    else:
        todos = frappe.get_all("ToDo", filters={"status": status}, 
                               fields=["name", "description", "status"])
    
    return {"todos": todos, "count": len(todos)}

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
```

### Step 3: Register Endpoint

Add the MCP endpoint handler:

```python
# todo_app/todo_app/mcp.py (add to existing file)

@mcp.register()
def handle_mcp():
    """Entry point for MCP requests."""
    # Import modules containing tools (if in separate files)
    # import todo_app.tools.todo_tools
    pass  # Tools already imported in this file
```

### Step 4: Test Your Server

Your MCP server is now available at:

```
http://<SITE_NAME>:<PORT>/api/method/todo_app.mcp.handle_mcp
```

For local development:

```
http://localhost:8000/api/method/todo_app.mcp.handle_mcp
```

---

## Core Concepts

### 1. The MCP Class

The `MCP` class orchestrates everything:

```python
from frappe_mcp import MCP

mcp = MCP(name="my-mcp-server")
```

**Parameters**:
- `name`: Unique identifier for your MCP server

### 2. Tools

Tools are functions that LLMs can call. Each tool needs:

- **Name**: Identifier for the tool
- **Description**: What the tool does
- **Input Schema**: JSON Schema defining parameters
- **Function**: The actual Python function to execute

### 3. Input Schema

Describes the parameters your tool accepts. Frappe MCP auto-generates this from:

- Type annotations (`int`, `str`, `bool`, etc.)
- Docstring parameter descriptions (Google style)

Example:

```python
@mcp.tool()
def search_items(query: str, limit: int = 10):
    """Search for items in the database.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return
    """
    pass
```

Auto-generated schema:

```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Search query string"
    },
    "limit": {
      "type": "integer",
      "description": "Maximum number of results to return"
    }
  },
  "required": ["query"]
}
```

### 4. Endpoints

The `@mcp.register()` decorator marks your MCP entry point:

```python
@mcp.register(allow_guest=False, xss_safe=False)
def handle_mcp():
    import app.tools.tools  # Import tool definitions
```

**Parameters**:
- `allow_guest`: Allow unauthenticated access (use only for testing)
- `xss_safe`: Skip XSS sanitization

---

## Building Your First MCP Server

Let's build a complete inventory management MCP server.

### Project Structure

```
inventory_app/
├── inventory_app/
│   ├── __init__.py
│   ├── hooks.py
│   ├── mcp.py              # MCP instance and endpoint
│   └── tools/
│       ├── __init__.py
│       ├── item_tools.py   # Item-related tools
│       └── stock_tools.py  # Stock-related tools
```

### Step 1: Create MCP Instance

```python
# inventory_app/inventory_app/mcp.py
import frappe_mcp

mcp = frappe_mcp.MCP("inventory-mcp")

@mcp.register()
def handle_mcp():
    """MCP endpoint handler."""
    import inventory_app.tools.item_tools
    import inventory_app.tools.stock_tools
```

### Step 2: Create Item Tools

```python
# inventory_app/inventory_app/tools/item_tools.py
from inventory_app.mcp import mcp
import frappe

@mcp.tool()
def search_items(search_term: str, item_group: str = None):
    """Search for items by name or code.
    
    Args:
        search_term: Text to search in item name or code
        item_group: Optional filter by item group
    """
    filters = {"item_name": ["like", f"%{search_term}%"]}
    
    if item_group:
        filters["item_group"] = item_group
    
    items = frappe.get_all(
        "Item",
        filters=filters,
        fields=["name", "item_name", "item_group", "stock_uom"],
        limit=20
    )
    
    return {
        "items": items,
        "count": len(items)
    }

@mcp.tool()
def get_item_details(item_code: str):
    """Get detailed information about a specific item.
    
    Args:
        item_code: The item code to look up
    """
    if not frappe.db.exists("Item", item_code):
        return {"error": f"Item {item_code} not found"}
    
    item = frappe.get_doc("Item", item_code)
    
    return {
        "item_code": item.name,
        "item_name": item.item_name,
        "description": item.description,
        "item_group": item.item_group,
        "stock_uom": item.stock_uom,
        "standard_rate": item.standard_rate,
        "is_stock_item": item.is_stock_item
    }

@mcp.tool()
def create_item(item_name: str, item_group: str, stock_uom: str = "Nos"):
    """Create a new item in the system.
    
    Args:
        item_name: Name of the item
        item_group: Item group classification
        stock_uom: Unit of measurement (default: Nos)
    """
    try:
        item = frappe.get_doc({
            "doctype": "Item",
            "item_name": item_name,
            "item_group": item_group,
            "stock_uom": stock_uom,
            "is_stock_item": 1
        })
        item.insert()
        frappe.db.commit()
        
        return {
            "success": True,
            "item_code": item.name,
            "message": f"Item {item.name} created successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

### Step 3: Create Stock Tools

```python
# inventory_app/inventory_app/tools/stock_tools.py
from inventory_app.mcp import mcp
import frappe

@mcp.tool()
def get_stock_balance(item_code: str, warehouse: str = None):
    """Get current stock balance for an item.
    
    Args:
        item_code: The item code
        warehouse: Optional specific warehouse (returns all if not specified)
    """
    from erpnext.stock.utils import get_stock_balance
    
    if warehouse:
        balance = get_stock_balance(item_code, warehouse)
        return {
            "item_code": item_code,
            "warehouse": warehouse,
            "balance": balance
        }
    else:
        warehouses = frappe.get_all("Warehouse", fields=["name"])
        balances = []
        
        for wh in warehouses:
            balance = get_stock_balance(item_code, wh.name)
            if balance > 0:
                balances.append({
                    "warehouse": wh.name,
                    "balance": balance
                })
        
        return {
            "item_code": item_code,
            "total_warehouses": len(balances),
            "balances": balances
        }

@mcp.tool()
def get_low_stock_items(threshold: int = 10):
    """Get items with stock below threshold.
    
    Args:
        threshold: Minimum stock quantity threshold
    """
    low_stock = frappe.db.sql("""
        SELECT item_code, warehouse, actual_qty
        FROM `tabBin`
        WHERE actual_qty < %s
        ORDER BY actual_qty ASC
        LIMIT 50
    """, (threshold,), as_dict=True)
    
    return {
        "threshold": threshold,
        "count": len(low_stock),
        "items": low_stock
    }
```

### Step 4: Test the Server

```bash
# In your frappe bench directory
source ./env/bin/activate
frappe-mcp check --app inventory_app --verbose
```

---

## Working with Tools

### Method 1: Using `@mcp.tool()` Decorator

**Basic Usage**:

```python
@mcp.tool()
def simple_tool(param1: str):
    """Tool description."""
    return {"result": param1}
```

**With Custom Name**:

```python
@mcp.tool(name="custom_name")
def my_function(param: str):
    """Description."""
    return {"result": param}
```

**With Manual Input Schema**:

```python
@mcp.tool(
    name="advanced_tool",
    description="A more complex tool",
    input_schema={
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {"type": "string"}
            },
            "options": {
                "type": "object",
                "properties": {
                    "sort": {"type": "boolean"},
                    "limit": {"type": "integer"}
                }
            }
        },
        "required": ["items"]
    }
)
def process_items(items, options=None):
    """Process a list of items with optional settings."""
    if options and options.get("sort"):
        items = sorted(items)
    
    if options and options.get("limit"):
        items = items[:options["limit"]]
    
    return {"processed_items": items}
```

**With Tool Annotations**:

```python
from frappe_mcp import ToolAnnotations

@mcp.tool(
    annotations=ToolAnnotations(
        title="Delete Customer Record",
        destructiveHint=True,
        idempotentHint=False
    )
)
def delete_customer(customer_id: str):
    """Permanently delete a customer record.
    
    Args:
        customer_id: The customer ID to delete
    """
    import frappe
    frappe.delete_doc("Customer", customer_id)
    return {"deleted": customer_id}
```

**Tool Annotation Types**:

- `title`: Human-readable tool title
- `readOnlyHint`: Tool only reads data, doesn't modify
- `destructiveHint`: Tool performs destructive operations
- `idempotentHint`: Safe to call multiple times with same params
- `openWorldHint`: Tool interacts with external systems

### Method 2: Using `mcp.add_tool()`

Manually define and register tools:

```python
from frappe_mcp import Tool, ToolAnnotations

def calculate_tax(amount: float, tax_rate: float):
    """Calculate tax on an amount."""
    return {"tax": amount * tax_rate, "total": amount * (1 + tax_rate)}

# Define tool
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

# Register tool
mcp.add_tool(tax_tool)
```

### Complex Parameter Types

**Arrays**:

```python
@mcp.tool()
def process_batch(item_codes: list[str], warehouse: str):
    """Process multiple items at once.
    
    Args:
        item_codes: List of item codes to process
        warehouse: Target warehouse
    """
    results = []
    for code in item_codes:
        # Process each item
        results.append({"item": code, "status": "processed"})
    return {"results": results}
```

**Nested Objects**:

```python
@mcp.tool(
    input_schema={
        "type": "object",
        "properties": {
            "customer": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "address": {
                        "type": "object",
                        "properties": {
                            "street": {"type": "string"},
                            "city": {"type": "string"}
                        }
                    }
                },
                "required": ["name", "email"]
            }
        },
        "required": ["customer"]
    }
)
def create_customer(customer):
    """Create a new customer with address."""
    import frappe
    
    cust = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": customer["name"],
        "email_id": customer["email"]
    })
    cust.insert()
    
    return {"customer_id": cust.name}
```

**Enumerations**:

```python
@mcp.tool(
    input_schema={
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["Open", "Closed", "Pending"],
                "description": "Filter by status"
            }
        },
        "required": ["status"]
    }
)
def filter_by_status(status):
    """Get items filtered by status."""
    import frappe
    return frappe.get_all("ToDo", filters={"status": status})
```

---

## Authentication Setup

### OAuth2 Authentication (Recommended)

If your Frappe instance has OAuth2 support (frappe#33188):

1. **No additional setup needed** - OAuth2 is automatically available
2. Use the MCP Inspector or any OAuth2 client to authenticate
3. Follow the Quick OAuth Flow in the inspector

### Manual OAuth Client Registration

For older Frappe versions:

1. Navigate to **OAuth Client** doctype
2. Create a new client:
   - **App Name**: Your MCP Client
   - **Client ID**: Auto-generated
   - **Client Secret**: Auto-generated
   - **Redirect URIs**: Add your client's redirect URI
   - **Grant Types**: Select "Authorization Code"
   - **Scopes**: Select appropriate scopes

3. Use these credentials in your MCP client

### Guest Access (Testing Only)

For development/testing only:

```python
@mcp.register(allow_guest=True)
def handle_mcp():
    """WARNING: This bypasses authentication!"""
    import app.tools
```

**⚠️ Never use `allow_guest=True` in production!**

---

## Testing and Debugging

### Using the CLI Tool

Frappe MCP includes a powerful CLI for validation:

```bash
# Check all apps
frappe-mcp check

# Check specific app
frappe-mcp check --app my_app

# Verbose output with schemas
frappe-mcp check --app my_app --verbose
```

**CLI checks**:
- ✅ Frappe environment detected
- ✅ Apps using frappe_mcp found
- ✅ MCP handlers discovered
- ✅ Tools registered correctly
- ✅ Input schemas valid
- ✅ Docstrings formatted properly

### Using MCP Inspector

The official MCP Inspector is a web-based testing tool:

**Setup**:

1. Install the inspector:
```bash
npx @modelcontextprotocol/inspector
```

2. Configure connection:
   - **Transport**: Streamable HTTP
   - **URL**: `http://localhost:8000/api/method/app.mcp.handle_mcp`
   - **Auth**: Quick OAuth Flow

3. Test your tools:
   - View available tools
   - Call tools with parameters
   - Inspect responses

### Manual Testing with cURL

Test the `/api/method/app.mcp.handle_mcp` endpoint:

**List Tools**:

```bash
curl -X POST http://localhost:8000/api/method/app.mcp.handle_mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

**Call a Tool**:

```bash
curl -X POST http://localhost:8000/api/method/app.mcp.handle_mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "get_todos",
      "arguments": {
        "status": "Open"
      }
    }
  }'
```

### Debugging Tips

**Enable Frappe Debug Mode**:

```bash
bench --site your-site set-config developer_mode 1
```

**Add Logging**:

```python
@mcp.tool()
def debug_tool(param: str):
    """Tool with logging."""
    import frappe
    
    frappe.logger().info(f"Tool called with: {param}")
    
    try:
        result = process_something(param)
        frappe.logger().info(f"Result: {result}")
        return result
    except Exception as e:
        frappe.logger().error(f"Error: {str(e)}")
        raise
```

**Check Frappe Logs**:

```bash
# In bench directory
tail -f logs/web.error.log
```

---

## Advanced Topics

### Using Frappe MCP in Non-Frappe Werkzeug Apps

You can use Frappe MCP in any Werkzeug-based application:

```python
from werkzeug.wrappers import Request, Response
from frappe_mcp import MCP

mcp = MCP("my-werkzeug-mcp")

@mcp.tool()
def example_tool(param: str):
    """Example tool."""
    return {"result": param}

@app.route('/mcp', methods=['POST'])
def handle_mcp_request():
    request = Request(environ)
    response = Response()
    return mcp.handle(request, response)
```

### Multiple MCP Endpoints

Create multiple MCP instances for different functionalities:

```python
# sales_mcp.py
sales_mcp = frappe_mcp.MCP("sales-mcp")

@sales_mcp.tool()
def create_order(customer: str):
    """Create sales order."""
    pass

@sales_mcp.register()
def handle_sales_mcp():
    import app.tools.sales_tools

# inventory_mcp.py
inventory_mcp = frappe_mcp.MCP("inventory-mcp")

@inventory_mcp.tool()
def check_stock(item: str):
    """Check stock levels."""
    pass

@inventory_mcp.register()
def handle_inventory_mcp():
    import app.tools.inventory_tools
```

Endpoints:
- Sales: `/api/method/app.sales_mcp.handle_sales_mcp`
- Inventory: `/api/method/app.inventory_mcp.handle_inventory_mcp`

### Error Handling

**Graceful Error Returns**:

```python
@mcp.tool()
def safe_tool(item_code: str):
    """Tool with error handling.
    
    Args:
        item_code: Item to process
    """
    import frappe
    
    try:
        if not frappe.db.exists("Item", item_code):
            return {
                "success": False,
                "error": "Item not found",
                "error_type": "NOT_FOUND"
            }
        
        item = frappe.get_doc("Item", item_code)
        
        return {
            "success": True,
            "data": {
                "name": item.name,
                "description": item.description
            }
        }
        
    except frappe.PermissionError:
        return {
            "success": False,
            "error": "Permission denied",
            "error_type": "PERMISSION_ERROR"
        }
    except Exception as e:
        frappe.log_error(title="MCP Tool Error")
        return {
            "success": False,
            "error": "Internal server error",
            "error_type": "INTERNAL_ERROR"
        }
```

### Working with File Uploads

Handle file operations in tools:

```python
@mcp.tool()
def process_document(file_url: str):
    """Process an uploaded document.
    
    Args:
        file_url: URL to the uploaded file
    """
    import frappe
    import requests
    
    # Download file
    response = requests.get(file_url)
    
    # Create File doc
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": "processed_document.pdf",
        "content": response.content,
        "is_private": 1
    })
    file_doc.save()
    
    return {
        "file_url": file_doc.file_url,
        "file_name": file_doc.file_name
    }
```

### Batch Operations

Process multiple items efficiently:

```python
@mcp.tool()
def batch_update_prices(updates: list):
    """Update prices for multiple items.
    
    Args:
        updates: List of {item_code, new_price} objects
    """
    import frappe
    
    results = {
        "successful": [],
        "failed": []
    }
    
    for update in updates:
        try:
            item = frappe.get_doc("Item", update["item_code"])
            item.standard_rate = update["new_price"]
            item.save()
            
            results["successful"].append(update["item_code"])
        except Exception as e:
            results["failed"].append({
                "item_code": update["item_code"],
                "error": str(e)
            })
    
    frappe.db.commit()
    
    return {
        "total": len(updates),
        "successful_count": len(results["successful"]),
        "failed_count": len(results["failed"]),
        "details": results
    }
```

---

## Best Practices

### 1. Tool Design

**Keep Tools Focused**:
```python
# ❌ Bad: Tool does too much
@mcp.tool()
def manage_customer(action: str, customer_id: str, data: dict):
    if action == "create":
        # create logic
    elif action == "update":
        # update logic
    elif action == "delete":
        # delete logic

# ✅ Good: Separate focused tools
@mcp.tool()
def create_customer(name: str, email: str):
    """Create a new customer."""
    pass

@mcp.tool()
def update_customer(customer_id: str, data: dict):
    """Update customer details."""
    pass

@mcp.tool()
def delete_customer(customer_id: str):
    """Delete a customer."""
    pass
```

**Use Clear Descriptions**:
```python
# ❌ Bad: Vague description
@mcp.tool()
def process(data: str):
    """Processes data."""
    pass

# ✅ Good: Clear, specific description
@mcp.tool()
def validate_email_address(email: str):
    """Validate an email address format and check if domain exists.
    
    Returns validation status and any error messages.
    
    Args:
        email: Email address to validate
    """
    pass
```

### 2. Error Handling

**Always Return Structured Responses**:
```python
@mcp.tool()
def get_customer(customer_id: str):
    """Get customer details."""
    import frappe
    
    # ✅ Structured response
    if not frappe.db.exists("Customer", customer_id):
        return {
            "success": False,
            "error": "Customer not found",
            "customer_id": customer_id
        }
    
    customer = frappe.get_doc("Customer", customer_id)
    
    return {
        "success": True,
        "data": {
            "name": customer.name,
            "email": customer.email_id
        }
    }
```

### 3. Performance

**Limit Result Sets**:
```python
@mcp.tool()
def search_items(query: str, limit: int = 20):
    """Search items with pagination.
    
    Args:
        query: Search query
        limit: Maximum results (default: 20, max: 100)
    """
    import frappe
    
    # Cap the limit
    limit = min(limit, 100)
    
    items = frappe.get_all(
        "Item",
        filters={"item_name": ["like", f"%{query}%"]},
        limit=limit
    )
    
    return {"items": items, "count": len(items)}
```

**Use Database Queries Efficiently**:
```python
# ❌ Bad: Multiple queries
@mcp.tool()
def get_item_with_stock(item_code: str):
    item = frappe.get_doc("Item", item_code)
    stock = frappe.get_all("Bin", filters={"item_code": item_code})
    return {"item": item, "stock": stock}

# ✅ Good: Single optimized query
@mcp.tool()
def get_item_with_stock(item_code: str):
    data = frappe.db.sql("""
        SELECT i.name, i.item_name, b.warehouse, b.actual_qty
        FROM `tabItem` i
        LEFT JOIN `tabBin` b ON i.name = b.item_code
        WHERE i.name = %s
    """, item_code, as_dict=True)
    
    return {"data": data}
```

### 4. Security

**Validate Permissions**:
```python
@mcp.tool()
def delete_document(doctype: str, name: str):
    """Delete a document with permission check.
    
    Args:
        doctype: Document type
        name: Document name
    """
    import frappe
    
    # Check permissions
    if not frappe.has_permission(doctype, "delete", name):
        return {
            "success": False,
            "error": "Insufficient permissions"
        }
    
    frappe.delete_doc(doctype, name)
    return {"success": True}
```

**Sanitize Inputs**:
```python
@mcp.tool()
def search_by_name(name: str):
    """Search with input validation.
    
    Args:
        name: Name to search for
    """
    import frappe
    import re
    
    # Sanitize input
    name = frappe.utils.cstr(name).strip()
    
    # Validate format
    if not re.match(r'^[a-zA-Z0-9\s\-]+$', name):
        return {
            "success": False,
            "error": "Invalid characters in search term"
        }
    
    # Proceed with search
    results = frappe.get_all("Customer", filters={"name": name})
    return {"success": True, "results": results}
```

### 5. Documentation

**Use Google-Style Docstrings**:
```python
@mcp.tool()
def calculate_shipping(weight: float, destination: str, express: bool = False):
    """Calculate shipping cost based on weight and destination.
    
    This tool uses current shipping rates and applies any active
    promotions or discounts.
    
    Args:
        weight: Package weight in kilograms
        destination: Destination country code (ISO 3166-1 alpha-2)
        express: Whether to use express shipping (default: False)
    
    Returns:
        Dictionary containing:
        - cost: Shipping cost in USD
        - estimated_days: Delivery time estimate
        - carrier: Recommended shipping carrier
    """
    # Implementation
    pass
```

---

## Troubleshooting

### Common Issues

**Issue: Tools not appearing**

```bash
# Check if tools are registered
frappe-mcp check --app your_app --verbose

# Ensure imports are correct
@mcp.register()
def handle_mcp():
    import app.tools.your_tools  # Make sure this import happens
```

**Issue: Schema generation fails**

```python
# Ensure type hints are present
@mcp.tool()
def broken_tool(param):  # ❌ No type hint
    pass

@mcp.tool()
def fixed_tool(param: str):  # ✅ Type hint present
    pass
```

**Issue: Authentication fails**

```bash
# Check OAuth client setup
bench --site your-site console

>>> frappe.get_all("OAuth Client")
# Verify client exists

# For testing, temporarily allow guest access
@mcp.register(allow_guest=True)
def handle_mcp():
    pass
```

**Issue: Endpoint not found**

```bash
# Verify endpoint URL format
# Should be: /api/method/APP_NAME.MODULE.FUNCTION
# Example: /api/method/todo_app.mcp.handle_mcp

# Check if site is correct
bench --site your-site list-apps
```

**Issue: JSON-RPC errors**

```python
# Enable detailed error logging
import frappe

@mcp.tool()
def debug_tool(param: str):
    try:
        # Your logic
        pass
    except Exception as e:
        frappe.log_error(
            title=f"MCP Tool Error: debug_tool",
            message=frappe.get_traceback()
        )
        raise
```

### Debugging Checklist

- [ ] Frappe environment activated
- [ ] App installed: `bench --site your-site list-apps`
- [ ] frappe-mcp package installed: `pip list | grep frappe-mcp`
- [ ] MCP instance created in app
- [ ] Tools imported in `@mcp.register()` function
- [ ] Endpoint accessible: Test with curl or browser
- [ ] OAuth client configured (if not using guest mode)
- [ ] CLI validation passed: `frappe-mcp check`

---

## Example: Complete ERP Integration

Here's a complete example integrating sales, inventory, and customer management:

```python
# erp_app/erp_app/mcp.py
import frappe_mcp

mcp = frappe_mcp.MCP("erp-assistant")

@mcp.register()
def handle_mcp():
    """Main MCP endpoint."""
    import erp_app.tools.sales
    import erp_app.tools.inventory
    import erp_app.tools.customers
```

```python
# erp_app/erp_app/tools/sales.py
from erp_app.mcp import mcp
import frappe

@mcp.tool()
def create_sales_order(customer: str, items: list, delivery_date: str):
    """Create a new sales order.
    
    Args:
        customer: Customer ID
        items: List of {item_code, qty, rate} dictionaries
        delivery_date: Expected delivery date (YYYY-MM-DD)
    """
    so = frappe.get_doc({
        "doctype": "Sales Order",
        "customer": customer,
        "delivery_date": delivery_date,
        "items": [
            {
                "item_code": item["item_code"],
                "qty": item["qty"],
                "rate": item["rate"]
            }
            for item in items
        ]
    })
    
    so.insert()
    so.submit()
    
    return {
        "success": True,
        "sales_order": so.name,
        "total": so.grand_total
    }

@mcp.tool()
def get_sales_analytics(from_date: str, to_date: str):
    """Get sales analytics for date range.
    
    Args:
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
    """
    analytics = frappe.db.sql("""
        SELECT 
            DATE(posting_date) as date,
            COUNT(*) as order_count,
            SUM(grand_total) as total_sales,
            AVG(grand_total) as avg_order_value
        FROM `tabSales Order`
        WHERE posting_date BETWEEN %s AND %s
        AND docstatus = 1
        GROUP BY DATE(posting_date)
        ORDER BY date
    """, (from_date, to_date), as_dict=True)
    
    return {
        "period": {"from": from_date, "to": to_date},
        "analytics": analytics
    }
```

```python
# erp_app/erp_app/tools/inventory.py
from erp_app.mcp import mcp
from erp_app.tools.notifications import send_alert
import frappe

@mcp.tool()
def check_inventory_levels(warehouse: str = None):
    """Check current inventory levels with low stock alerts.
    
    Args:
        warehouse: Specific warehouse (optional, checks all if not provided)
    """
    filters = {"actual_qty": [">", 0]}
    if warehouse:
        filters["warehouse"] = warehouse
    
    stock = frappe.db.sql("""
        SELECT 
            b.item_code,
            i.item_name,
            b.warehouse,
            b.actual_qty,
            i.stock_uom,
            CASE 
                WHEN b.actual_qty < 10 THEN 'LOW'
                WHEN b.actual_qty < 50 THEN 'MEDIUM'
                ELSE 'GOOD'
            END as stock_status
        FROM `tabBin` b
        JOIN `tabItem` i ON b.item_code = i.name
        WHERE b.actual_qty > 0
        ORDER BY b.actual_qty ASC
    """, as_dict=True)
    
    low_stock = [s for s in stock if s.stock_status == 'LOW']
    
    return {
        "total_items": len(stock),
        "low_stock_count": len(low_stock),
        "stock_levels": stock[:50],  # Limit results
        "low_stock_items": low_stock
    }

@mcp.tool()
def create_stock_entry(item_code: str, qty: float, warehouse: str, 
                       entry_type: str = "Material Receipt"):
    """Create a stock entry.
    
    Args:
        item_code: Item code
        qty: Quantity
        warehouse: Target warehouse
        entry_type: Entry type (Material Receipt, Material Issue, etc.)
    """
    se = frappe.get_doc({
        "doctype": "Stock Entry",
        "stock_entry_type": entry_type,
        "items": [{
            "item_code": item_code,
            "qty": qty,
            "t_warehouse": warehouse if entry_type == "Material Receipt" else None,
            "s_warehouse": warehouse if entry_type == "Material Issue" else None
        }]
    })
    
    se.insert()
    se.submit()
    
    return {
        "success": True,
        "stock_entry": se.name,
        "item": item_code,
        "qty": qty
    }
```

```python
# erp_app/erp_app/tools/customers.py
from erp_app.mcp import mcp
import frappe

@mcp.tool()
def get_customer_insights(customer_id: str):
    """Get comprehensive customer insights.
    
    Args:
        customer_id: Customer ID
    """
    # Customer details
    customer = frappe.get_doc("Customer", customer_id)
    
    # Purchase history
    orders = frappe.get_all(
        "Sales Order",
        filters={"customer": customer_id, "docstatus": 1},
        fields=["name", "posting_date", "grand_total"],
        order_by="posting_date desc",
        limit=10
    )
    
    # Analytics
    stats = frappe.db.sql("""
        SELECT 
            COUNT(*) as total_orders,
            SUM(grand_total) as lifetime_value,
            AVG(grand_total) as avg_order_value,
            MAX(posting_date) as last_order_date
        FROM `tabSales Order`
        WHERE customer = %s AND docstatus = 1
    """, customer_id, as_dict=True)[0]
    
    return {
        "customer": {
            "id": customer.name,
            "name": customer.customer_name,
            "email": customer.email_id,
            "phone": customer.mobile_no
        },
        "statistics": stats,
        "recent_orders": orders
    }

@mcp.tool()
def create_customer(customer_name: str, email: str, phone: str = None):
    """Create a new customer.
    
    Args:
        customer_name: Customer's full name
        email: Email address
        phone: Phone number (optional)
    """
    customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": customer_name,
        "email_id": email,
        "mobile_no": phone,
        "customer_group": "Individual",
        "territory": "All Territories"
    })
    
    customer.insert()
    
    return {
        "success": True,
        "customer_id": customer.name,
        "message": f"Customer {customer_name} created successfully"
    }
```

---

## Conclusion

Frappe MCP makes it simple to turn your Frappe applications into powerful MCP servers that LLMs can interact with. Key takeaways:

1. **Simple Setup**: Install, create MCP instance, register tools, done
2. **Type-Safe**: Auto-generates schemas from Python type hints
3. **Frappe-Native**: Designed specifically for Frappe Framework
4. **Testing Tools**: Built-in CLI for validation and debugging
5. **Flexible**: Supports various tool patterns and complexity levels

### Next Steps

- Explore the [official MCP documentation](https://modelcontextprotocol.io/)
- Join the [Frappe community](https://discuss.frappe.io/)
- Contribute to [Frappe MCP on GitHub](https://github.com/frappe/mcp)

### Additional Resources

- [Frappe Framework Documentation](https://docs.frappe.io/framework)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/specification)
- [MCP Registry](https://github.com/mcp)

---

*Tutorial Version: 1.0*  
*Last Updated: April 2026*  
*License: MIT*
