#!/usr/bin/env python3
"""Simple test script to verify MCP server connection and list tools."""

import json
import requests

MCP_URL = "http://localhost:8001/api/method/todo_app.mcp.handle_mcp"


def send_request(method, params=None):
	payload = {
		"jsonrpc": "2.0",
		"id": 1,
		"method": method,
	}
	if params:
		payload["params"] = params

	response = requests.post(MCP_URL, json=payload, headers={"Content-Type": "application/json"})
	response.raise_for_status()
	return response.json()


def main():
	print("Testing MCP Server Connection...")
	print(f"URL: {MCP_URL}\n")

	try:
		print("1. Initializing connection...")
		result = send_request(
			"initialize",
			{
				"protocolVersion": "2024-11-05",
				"capabilities": {},
				"clientInfo": {"name": "test-client", "version": "1.0.0"},
			},
		)
		print(f"   Server info: {result.get('result', {})}\n")

		print("2. Listing available tools...")
		result = send_request("tools/list")
		tools = result.get("result", {}).get("tools", [])
		print(f"   Found {len(tools)} tools:\n")

		for tool in tools:
			print(f"   - {tool['name']}")
			print(f"     Description: {tool.get('description', 'N/A')}")
			print(f"     Parameters: {json.dumps(tool.get('inputSchema', {}), indent=10)}")
			print()

		print("3. Testing a tool call (get_todos)...")
		result = send_request("tools/call", {"name": "get_todos", "arguments": {"status": "Open"}})
		print(f"   Result: {json.dumps(result.get('result', {}), indent=4)}")

		print("\n✓ MCP server is working correctly!")

	except requests.exceptions.ConnectionError:
		print("✗ Error: Could not connect to MCP server")
		print("  Make sure the Frappe server is running on port 8001")
	except Exception as e:
		print(f"✗ Error: {e}")


if __name__ == "__main__":
	main()
