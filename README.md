### Todo App

This is a ToDo app with MCP (Model Context Protocol) tool integration for AI/LLM interactions.

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app todo_app
```

### Available MCP Tools

#### Todo Tools (`todo_app/mcp.py`)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_todos` | Get all todos filtered by status | `status` (str, optional): Filter by status (Open, Closed, All). Default: "Open" |
| `create_todo` | Create a new TODO item | `description` (str, required): The TODO description<br>`priority` (str, optional): Priority level (Low, Medium, High). Default: "Medium" |
| `mark_done` | Mark a TODO as completed | `todo_id` (str, required): The ID of the TODO item |
| `simple_tool` | Simple test tool | `param1` (str, required): Any string parameter |
| `calculate_tax` | Calculate tax and total | `amount` (float, required): Base amount<br>`tax_rate` (float, required): Tax rate (e.g., 0.18 for 18%) |

#### Item Tools (`todo_app/tools/item_tools.py`)

| Tool | Description | Parameters |
|------|-------------|------------|
| `search_items` | Search for items by name | `search_term` (str, required): Text to search in item name<br>`item_group` (str, optional): Filter by item group |
| `get_item_details` | Get detailed item information | `item_code` (str, required): The item code |
| `create_item` | Create a new item | `item_code` (str, required): Item code<br>`item_name` (str, required): Item name<br>`item_group` (str, required): Item group<br>`stock_uom` (str, optional): Unit of measure. Default: "Nos" |

#### Customer Tools (`todo_app/tools/customers.py`)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_customer_insights` | Get comprehensive customer insights with purchase history and analytics | `customer_name` (str, required): Customer ID or name |
| `create_customer` | Create a new customer | `customer_name` (str, required): Customer name<br>`email` (str, required): Email address<br>`customer_type` (str, required): Type (Individual, Company, Partnership)<br>`phone` (str, optional): Phone number |

#### Stock Tools (`todo_app/tools/stock_tools.py`)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_stock_balance` | Get current stock balance for an item | `item_code` (str, required): Item code<br>`warehouse` (str, optional): Specific warehouse. If not provided, returns all warehouses |
| `get_low_stock_items` | Get items with stock below threshold | `threshold` (int, optional): Minimum stock quantity. Default: 10 |

### Testing Tools via Prompt

#### Using Groq API

```bash
export GROQ_API_KEY=your_api_key_here
source env/bin/activate
python apps/todo_app/llm_client.py
```

Optional: Set a different model:
```bash
GROQ_API_KEY=gsk_xxx GROQ_MODEL=mixtral-8x7b-32768 python apps/todo_app/llm_client.py
```

Available Groq models:
- `llama-3.3-70b-versatile` (default, recommended)
- `mixtral-8x7b-32768`
- `llama-3.1-8b-instant`

#### Direct Tool Testing

```bash
source env/bin/activate
python apps/todo_app/test_mcp_connection.py
```

### Example Prompts

```
You: Show me all open todos
You: Create a todo to review the quarterly reports with high priority
You: Mark todo TODO-001 as done
You: Search for items with name "widget"
You: Get details for item_code "ABC-001"
You: Create an item with code "NEW-001", name "New Product", group "Products"
You: Calculate tax for 1000 with 18% rate
You: Get stock balance for item "ITEM-001"
You: Show low stock items with threshold of 5
You: Get customer insights for "Customer-001"
You: Create a new customer named John Doe with email john@example.com
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/todo_app
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit
