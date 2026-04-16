import json
import requests
from typing import Any, Optional


class MCPClient:
	def __init__(self, base_url: str, api_key: Optional[str] = None, api_secret: Optional[str] = None):
		self.base_url = base_url.rstrip("/")
		self.session = requests.Session()

		if api_key and api_secret:
			self.session.headers.update({"api_key": api_key, "api_secret": api_secret})

	def _send_request(self, method: str, params: Optional[dict] = None) -> dict:
		payload = {
			"jsonrpc": "2.0",
			"id": 1,
			"method": method,
		}
		if params:
			payload["params"] = params

		response = self.session.post(
			self.base_url, json=payload, headers={"Content-Type": "application/json"}
		)
		response.raise_for_status()
		data = response.json()
		# Frappe's API envelope wraps the raw response body as {"data": "...", "mimetype": ..., "status_code": ...}.
		# Older Frappe versions return the MCP JSON-RPC response directly. Detect and unwrap accordingly.
		if "status_code" in data and "data" in data:
			data = json.loads(data["data"])
		return data

	def initialize(self) -> dict:
		result = self._send_request(
			"initialize",
			{
				"protocolVersion": "2024-11-05",
				"capabilities": {},
				"clientInfo": {"name": "llm-mcp-client", "version": "1.0.0"},
			},
		)
		return result.get("result", {})

	def list_tools(self) -> list[dict]:
		result = self._send_request("tools/list")
		return result.get("result", {}).get("tools", [])

	def call_tool(self, tool_name: str, arguments: dict) -> Any:
		result = self._send_request("tools/call", {"name": tool_name, "arguments": arguments})
		return result.get("result", {})


class GroqToolInvoker:
	def __init__(self, mcp_client: MCPClient, model: str = "llama-3.3-70b-versatile"):
		self.base_url = "https://api.groq.com/openai/v1"
		self.model = model
		self.mcp = mcp_client
		self.tools = []
		self.system_prompt = """You have access to tools via the MCP server. 
When the user asks something that requires data or actions, use the available tools.
Available tools: get_todos, create_todo, mark_done, calculate_tax, search_items, get_item_details, create_item, get_stock_balance, get_low_stock_items
Always respond clearly with the results from the tools.
If no tool is needed, just answer directly."""

	def setup(self):
		self.mcp.initialize()
		self.tools = self.mcp.list_tools()
		return self.tools

	def _format_tools_for_groq(self) -> list[dict]:
		groq_tools = []
		for tool in self.tools:
			props = tool.get("inputSchema", {}).get("properties", {})
			required = tool.get("inputSchema", {}).get("required", [])

			properties = {}
			for param_name, param_info in props.items():
				param_type = param_info.get("type", "string")
				if param_type == "float":
					param_type = "number"
				properties[param_name] = {
					"type": param_type,
					"description": param_info.get("description", ""),
				}

			groq_tools.append(
				{
					"type": "function",
					"function": {
						"name": tool["name"],
						"description": tool.get("description", ""),
						"parameters": {"type": "object", "properties": properties, "required": required},
					},
				}
			)
		return groq_tools

	def chat(self, user_message: str, verbose: bool = False) -> str:
		if not self.tools:
			self.setup()

		messages = [
			{"role": "system", "content": self.system_prompt},
			{"role": "user", "content": user_message},
		]

		tools = self._format_tools_for_groq()

		headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

		payload = {"model": self.model, "messages": messages, "tools": tools}

		response = requests.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
		response.raise_for_status()
		result = response.json()

		assistant_message = result["choices"][0]["message"]
		messages.append(assistant_message)

		if assistant_message.get("tool_calls"):
			for tool_call in assistant_message["tool_calls"]:
				tool_name = tool_call["function"]["name"]
				arguments = json.loads(tool_call["function"]["arguments"])

				if verbose:
					print(f"\n[Tool Call] {tool_name}")
					print(f"Arguments: {arguments}")

				tool_result = self.mcp.call_tool(tool_name, arguments)

				if verbose:
					print(f"Result: {json.dumps(tool_result, indent=2)}")

				messages.append(
					{"role": "tool", "tool_call_id": tool_call["id"], "content": json.dumps(tool_result)}
				)

			response = requests.post(
				f"{self.base_url}/chat/completions",
				json={"model": self.model, "messages": messages},
				headers=headers,
			)
			response.raise_for_status()
			result = response.json()

			return result["choices"][0]["message"].get("content", "No response")

		return assistant_message.get("content", "No response")


def main():
	import os

	MCP_URL = os.environ.get("MCP_URL", "http://localhost:8001/api/method/todo_app.mcp.handle_mcp")
	GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
	GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

	if not GROQ_API_KEY:
		print("Error: GROQ_API_KEY environment variable not set")
		print("Set it with: export GROQ_API_KEY=your_api_key")
		return

	print("=" * 50)
	print("MCP + Groq Tool Invoker")
	print("=" * 50)

	print(f"Connecting to MCP server: {MCP_URL}")
	mcp = MCPClient(MCP_URL)
	invoker = GroqToolInvoker(mcp, GROQ_MODEL)
	invoker.api_key = GROQ_API_KEY

	print(f"Using Groq model: {GROQ_MODEL}")
	print("Fetching available tools...")
	tools = invoker.setup()
	print(f"Found {len(tools)} tools:")
	for tool in tools:
		print(f"  - {tool['name']}")

	print("\n" + "=" * 50)
	print("Chat with the LLM (type 'quit' to exit)")
	print("=" * 50 + "\n")

	while True:
		try:
			user_input = input("You: ")
		except EOFError:
			break

		if user_input.lower() in ["quit", "exit", "q"]:
			break

		if not user_input.strip():
			continue

		try:
			response = invoker.chat(user_input, verbose=True)
			print(f"\nAssistant: {response}\n")
		except requests.exceptions.HTTPError as e:
			print(f"Error: {e.response.text}\n")
		except Exception as e:
			print(f"Error: {e}\n")


if __name__ == "__main__":
	main()
