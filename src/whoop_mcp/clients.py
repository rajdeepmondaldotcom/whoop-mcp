"""Auto-configuration of MCP clients (Claude Desktop, Claude Code).

Used by ``whoop-mcp setup`` so a user never has to hand-edit JSON. Edits are
conservative: existing config is parsed leniently, backed up to ``.bak``
before the first change, and written atomically.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import sys
from pathlib import Path

SERVER_KEY = "whoop"


def find_binary() -> str:
    """Absolute path to the installed ``whoop-mcp`` command."""
    on_path = shutil.which("whoop-mcp")
    if on_path:
        return str(Path(on_path).resolve())
    candidate = Path(sys.argv[0]).resolve()
    if candidate.name == "whoop-mcp" and candidate.exists():
        return str(candidate)
    sibling = Path(sys.executable).parent / "whoop-mcp"
    if sibling.exists():
        return str(sibling.resolve())
    return "whoop-mcp"  # hope it's on the client's PATH


def claude_desktop_config_path() -> Path:
    system = platform.system()
    if system == "Darwin":
        return Path("~/Library/Application Support/Claude/claude_desktop_config.json").expanduser()
    if system == "Windows":
        appdata = os.environ.get("APPDATA", "~\\AppData\\Roaming")
        return Path(appdata).expanduser() / "Claude" / "claude_desktop_config.json"
    return Path("~/.config/Claude/claude_desktop_config.json").expanduser()


def claude_desktop_detected() -> bool:
    return claude_desktop_config_path().parent.exists()


def install_into_claude_desktop(binary: str | None = None) -> tuple[Path, str]:
    """Add (or update) the whoop server entry in Claude Desktop's config.

    Returns (config_path, action) where action is one of "added", "updated",
    "unchanged".
    """
    binary = binary or find_binary()
    path = claude_desktop_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    config: dict = {}
    original_corrupt = False
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                config = loaded
        except (OSError, json.JSONDecodeError):
            # Keep the broken original safe and start fresh.
            original_corrupt = True
            shutil.copy2(path, path.with_suffix(".json.broken"))

    servers = config.setdefault("mcpServers", {})
    desired = {"command": binary, "args": ["serve"]}
    existing = servers.get(SERVER_KEY)
    if existing == desired:
        return path, "unchanged"
    action = "updated" if existing else "added"
    servers[SERVER_KEY] = desired

    # Never let a corrupt original overwrite the last *good* backup — the
    # .json.broken copy above already preserves the corrupt bytes.
    if path.exists() and not original_corrupt:
        shutil.copy2(path, path.with_suffix(".json.bak"))
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return path, action


def claude_code_detected() -> bool:
    return shutil.which("claude") is not None


def claude_code_command(binary: str | None = None) -> list[str]:
    binary = binary or find_binary()
    return ["claude", "mcp", "add", "--scope", "user", SERVER_KEY, "--", binary, "serve"]
