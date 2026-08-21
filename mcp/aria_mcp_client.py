"""
Aria MCP Client — integrates MCP server into agent.py
Handles tool discovery, permission dialogs, and communication
"""
import subprocess
import json
import threading
import queue
import tkinter as tk
from tkinter import messagebox

class MCPClient:
    def __init__(self):
        self.process = None
        self.request_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.tools = {}
        self.running = False
        
    def start(self):
        """Start the MCP server subprocess."""
        import sys, os
        server_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aria_mcp_server.py")
        if not os.path.exists(server_script):
            server_script = "aria_mcp_server.py"
        try:
            self.process = subprocess.Popen(
                [sys.executable, server_script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            self.running = True
            
            # Start background thread to read responses FIRST
            threading.Thread(target=self._read_responses, daemon=True).start()
            
            # Wait for server ready with timeout
            import time
            timeout = 5
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    # Non-blocking check for server ready message
                    time.sleep(0.1)
                    if hasattr(self, '_server_ready'):
                        print("✅ MCP Server connected")
                        self._discover_tools()
                        return True
                except:
                    pass
            
            print("⚠️ MCP Server timeout - continuing without it")
            return False
                
        except Exception as e:
            print(f"❌ MCP Server error: {e}")
            return False
    
    def _read_responses(self):
        """Background thread to read MCP server responses."""
        while self.running:
            try:
                line = self.process.stdout.readline()
                if not line:
                    break
                    
                msg = json.loads(line)
                
                # Handle server ready
                if msg.get("type") == "server_ready":
                    self._server_ready = True
                # Handle permission requests
                elif msg.get("type") == "permission_request":
                    self._handle_permission_request(msg)
                else:
                    # Regular response
                    self.response_queue.put(msg)
                    
            except Exception as e:
                print(f"MCP read error: {e}")
                break
    
    def _handle_permission_request(self, request):
        """Show permission request in console and get user response."""
        action = request.get("action", "unknown")
        details = request.get("details", {})
        
        # Format details for display
        print("\n" + "="*60)
        print("🔐 PERMISSION REQUEST")
        print("="*60)
        print(f"Action: {action}")
        for k, v in details.items():
            print(f"  {k}: {v}")
        print("="*60)
        
        # Get user input from console
        while True:
            response = input("Allow this action? (yes/no): ").strip().lower()
            if response in ['yes', 'y']:
                approved = True
                break
            elif response in ['no', 'n']:
                approved = False
                break
            else:
                print("Please type 'yes' or 'no'")
        
        # Send response to MCP server
        response_msg = {
            "approved": approved,
            "reason": "User approved" if approved else "User denied"
        }
        
        self.process.stdin.write(json.dumps(response_msg) + "\n")
        self.process.stdin.flush()
        
        status = "✅ APPROVED" if approved else "❌ DENIED"
        print(f"\n{status}\n")
    
    def _discover_tools(self):
        """Discover available tools from MCP server."""
        request = {"method": "tools/list", "params": {}}
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        
        # Wait for response
        try:
            response = self.response_queue.get(timeout=5)
            tools_list = response.get("tools", [])
            
            for tool in tools_list:
                self.tools[tool["name"]] = tool
            
            print(f"📋 Discovered {len(self.tools)} MCP tools")
            
        except queue.Empty:
            print("⚠️ Tool discovery timeout")
    
    def call_tool(self, tool_name, arguments):
        """Call an MCP tool."""
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}
        
        request = {
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        
        # Wait for response
        try:
            response = self.response_queue.get(timeout=30)
            return response
        except queue.Empty:
            return {"error": "Tool call timeout"}
    
    def get_tools_for_prompt(self):
        """Get tool descriptions formatted for AI prompt."""
        if not self.tools:
            return ""
        
        tool_descriptions = []
        for name, info in self.tools.items():
            params = info.get("parameters", {})
            param_str = ", ".join([f"{k}" for k in params.keys()])
            
            desc = f"- {name}({param_str}): {info.get('description', '')}"
            tool_descriptions.append(desc)
        
        return "\n".join(tool_descriptions)
    
    def stop(self):
        """Stop the MCP server."""
        self.running = False
        if self.process:
            self.process.terminate()
            self.process.wait()
