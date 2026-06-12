"""Fallback entry point. MCP clients use mcp_config (uvx) directly; this
stub does the same thing for clients that execute the entry point instead."""

import subprocess
import sys

if __name__ == "__main__":
    sys.exit(subprocess.run(["uvx", "whoop-mcp-server", "serve"]).returncode)
