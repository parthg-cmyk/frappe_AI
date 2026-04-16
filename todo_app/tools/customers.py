from todo_app.mcp import mcp
import frappe
import json
from typing import Optional


@mcp.tool()
def get_customer_insights(customer_name: str):
    """Get comprehensive customer insights.

    Args:
        customer_name (str): Id or Name of the customer, which can refer to an individual person, company, or organization.
    """
    # Customer details
    customer = frappe.get_doc("Customer", customer_name)

    # Purchase history
    orders = frappe.get_all(
        "Sales Order",
        filters={"customer": customer_name, "docstatus": 1},
        fields=["name", "delivery_date", "grand_total"],
        order_by="delivery_date desc",
        limit=10,
    )

    # Analytics
    stats = frappe.db.sql(
        """
        SELECT 
            COUNT(*) as total_orders,
            SUM(grand_total) as lifetime_value,
            AVG(grand_total) as avg_order_value,
            MAX(delivery_date) as last_order_date
        FROM `tabSales Order`
        WHERE customer = %s AND docstatus = 1
    """,
        customer_name,
        as_dict=True,
    )[0]

    return {
        "customer": {
            "id": customer.name,
            "name": customer.customer_name,
            "email": customer.email_id,
            "phone": customer.mobile_no,
        },
        "statistics": stats,
        "recent_orders": orders,
    }


@mcp.tool()
def create_customer(
    customer_name: str, email: str, customer_type: str, phone: Optional[str] = None
):
    """Create a new customer.

    Args:
        customer_name (str): Name of the customer (person, company, or organization)
        email (str): Email address
        customer_type (str): Type of customer (Individual, Company, Partnership)
        phone (str, optional): Phone number
    """

    try:
        # ✅ Normalize input
        customer_type = customer_type.capitalize()

        # ❗ Map Partnership → Company (ERPNext limitation)
        if customer_type == "Partnership":
            erp_customer_type = "Company"
            customer_group = "Commercial"  # or any valid group
        elif customer_type == "Company":
            erp_customer_type = "Company"
            customer_group = "Commercial"
        else:
            erp_customer_type = "Individual"
            customer_group = "Individual"

        # ✅ Check duplicate
        if frappe.db.exists("Customer", {"customer_name": customer_name}):
            return {
                "success": False,
                "error": f"Customer '{customer_name}' already exists",
            }

        # ✅ Ensure group exists (safe fallback)
        if not frappe.db.exists(
            "Customer Group", {"name": customer_group, "is_group": 0}
        ):
            customer_group = frappe.get_all(
                "Customer Group", filters={"is_group": 0}, pluck="name", limit=1
            )[0]

        customer = frappe.get_doc(
            {
                "doctype": "Customer",
                "customer_name": customer_name,
                "customer_type": erp_customer_type,
                "customer_group": customer_group,
                "territory": "All Territories",
                "email_id": email,
                "mobile_no": phone,
            }
        )

        customer.insert(ignore_permissions=True)  # TODO: remove this and enforce role-based access in production
        frappe.db.commit()

        return json.loads(
            json.dumps(
                {
                    "success": True,
                    "customer_id": customer.name,
                    "customer_type": erp_customer_type,
                    "message": f"Customer {customer_name} created successfully",
                },
                default=str,
            )
        )

    except Exception:
        return {"success": False, "error": frappe.get_traceback()}
