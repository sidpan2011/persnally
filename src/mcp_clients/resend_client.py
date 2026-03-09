"""
MCP Resend Client - handles email sending via Resend MCP server
"""

import asyncio
import json

import httpx


class MCPResendClient:
    """MCP client for Resend email sending"""

    def __init__(self, config):
        self.config = config
        self.mcp_server_path = "mcp_server/resend/mcp-send-email/build/index.js"
        self.mcp_process = None

    async def start_mcp_server(self):
        """Start the Resend MCP server"""
        try:
            # Start the MCP server process
            self.mcp_process = await asyncio.create_subprocess_exec(
                "node",
                self.mcp_server_path,
                "--key",
                self.config.RESEND_API_KEY,
                "--sender",
                "Persnally <updates@persnally.com>",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            print("✅ Resend MCP server started")
            return True
        except Exception as e:
            print(f"❌ Failed to start MCP server: {e}")
            return False

    async def stop_mcp_server(self):
        """Stop the Resend MCP server"""
        if self.mcp_process:
            self.mcp_process.terminate()
            await self.mcp_process.wait()
            print("✅ Resend MCP server stopped")

    async def send_email_via_mcp(self, to_email: str, subject: str, html_content: str, text_content: str = None):
        """Send email via MCP server"""
        if not self.mcp_process:
            print("❌ MCP server not started, falling back to HTTP")
            return await self._send_via_http(to_email, subject, html_content, text_content)

        # Create the MCP request
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "send-email",
                "arguments": {
                    "to": to_email,
                    "subject": subject,
                    "text": text_content or self._html_to_text(html_content),
                    "html": html_content,
                    "from": "Persnally <updates@persnally.com>",
                },
            },
        }

        # print(f"📤 Sending MCP request: {json.dumps(mcp_request, indent=2)}")

        try:
            # Send request to MCP server
            request_json = json.dumps(mcp_request) + "\n"
            self.mcp_process.stdin.write(request_json.encode())
            await self.mcp_process.stdin.drain()

            # Read response
            response_line = await self.mcp_process.stdout.readline()
            response = json.loads(response_line.decode().strip())

            print(f"📥 MCP response: {json.dumps(response, indent=2)}")

            if "error" in response:
                raise Exception(f"MCP Error: {response['error']}")

            # Check if the result indicates an error (like Resend 403)
            result = response.get("result", {})
            if result.get("isError", False):
                error_content = result.get("content", [{}])[0].get("text", "")
                if "403" in error_content or "You can only send testing emails" in error_content:
                    print("🔄 Resend test domain restriction detected, falling back to HTTP...")
                    return await self._send_via_http(to_email, subject, html_content, text_content)
                else:
                    raise Exception(f"MCP Server Error: {error_content}")

            return result

        except Exception as e:
            print(f"❌ MCP email sending failed: {e}")
            # Fallback to direct HTTP call
            print("🔄 Falling back to direct HTTP call...")
            return await self._send_via_http(to_email, subject, html_content, text_content)

    async def _send_via_http(self, to_email: str, subject: str, html_content: str, text_content: str = None):
        """Fallback: Send email via direct HTTP call"""
        headers = {"Authorization": f"Bearer {self.config.RESEND_API_KEY}", "Content-Type": "application/json"}

        payload = {
            "from": "Persnally <updates@persnally.com>",
            "to": [to_email],  # Send to actual user email
            "subject": subject,
            "html": html_content,
            "text": text_content or self._html_to_text(html_content),
        }

        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.resend.com/emails", headers=headers, json=payload)

            if response.status_code == 200:
                print("✅ Email sent successfully via HTTP fallback")
                return {"success": True}
            else:
                print(f"❌ HTTP fallback failed: {response.text}")
                return {"success": False, "error": response.text}

    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text (simple implementation)"""
        import re

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", html_content)
        # Clean up whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text
