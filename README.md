# whoop-mcp

**Your WHOOP data, in any AI.** A Model Context Protocol (MCP) server that connects everything WHOOP knows about you — recovery, sleep, strain, workouts, heart rate, sleep-stage and overnight sensor data — to **Claude**, **ChatGPT**, and any other MCP client.

Pure Python. Runs on your machine. Your health data and tokens never touch anyone else's server.

```text
You: give me the full picture of my health this quarter

AI → get_health_overview(days=90)
   ← Recovery 78% (green) today · recovery trending up, HRV improving
   ← sleep avg 7.4h (stable) · training load balanced (A:C 1.02)
   ← longest green streak: 11 days · strongest pattern: high-strain days
     correlate with lower next-morning recovery (r=-0.61, strong)
```

## Get started in 3 commands

```bash
git clone https://github.com/rajdeepmondaldotcom/whoop-mcp.git && cd whoop-mcp
uv tool install .          # or: pipx install .
whoop-mcp setup
```

That's it. `whoop-mcp setup` walks you through everything interactively:

1. **WHOOP app** — guides you through creating your free developer app (one time, ~2 minutes; it opens the dashboard for you and tells you exactly what to click), then stores the credentials with `0600` permissions.
2. **Authorize** — opens your browser to WHOOP's consent page; tokens are saved locally and auto-refresh forever after.
3. **Verify** — makes a live API call and shows your actual latest recovery, so you know it works before you leave the terminal.
4. **Connect your AI** — detects **Claude Desktop** and **Claude Code** and configures them *for you* (safely: existing config preserved, backup written). Prints copy-paste instructions for everything else.

Then ask your AI: *"How did I sleep last night?"*

Already added the server to Claude but skipped auth? Just ask: *"connect my WHOOP account"* — the `connect_whoop_account` tool opens the consent page right from chat.

## What your AI can do with it

**23 tools.** Every read endpoint in WHOOP API v2 — plus the analysis layer that turns records into answers.

### Holistic views
| Tool | What it answers |
| --- | --- |
| `get_health_overview` | **Start here.** Today's status + trend directions + training load + records + streaks + your strongest behavior↔physiology correlations, in one call |
| `get_daily_summary` | "How am I doing today?" — recovery, sleep, strain, workouts for any day |
| `get_weekly_report` | Monday–Sunday grid with averages and totals |
| `get_correlations` | "What actually affects my recovery?" — strain → next-morning recovery, sleep duration/consistency → recovery, HRV → recovery, with Pearson r and plain-English readings |
| `get_personal_records` | Bests, worsts, green-recovery streaks, totals over any window |
| `compare_periods` | "This month vs last month" across every metric, polarity-aware |

### Trends & analysis
| Tool | What it answers |
| --- | --- |
| `get_recovery_trends` | Recovery %, HRV, resting HR: stats, direction, confidence, unusual days |
| `get_sleep_trends` | Hours, performance, efficiency, consistency, sleep debt over time |
| `get_strain_trends` | Daily strain, calories, per-sport breakdown, acute:chronic load ratio |

### Records (every WHOOP v2 endpoint)
| Tool | What it answers |
| --- | --- |
| `get_recoveries` / `get_sleeps` / `get_workouts` / `get_cycles` | Filterable lists (date expressions, sport filter, nap filter) |
| `get_sleep` / `get_workout` / `get_cycle` | Single records — `get_cycle` joins its recovery + sleep; all take `include_raw` for the untouched API payload |
| `get_sleep_stream` | **Minute-level overnight sensor data**: heart-rate and skin-temperature curves, lowest HR and when it happened |
| `get_profile` | Name, email, height, weight, max HR |

### Data ownership & connection
| Tool | What it answers |
| --- | --- |
| `export_data` | Writes your complete history to local files: `data.json` (everything, raw + transformed), `daily_summary.csv`, `workouts.csv` — "export my last 2 years" just works |
| `get_connection_status` | Token state, scopes, live API check — first stop when something fails |
| `connect_whoop_account` | Browser OAuth from inside the chat |

Plus **4 resources** (`whoop://summary/today`, `whoop://recovery/latest`, `whoop://sleep/latest`, `whoop://profile`) and **4 prompts** (`morning_readiness`, `weekly_review`, `sleep_coach`, `training_planner`).

Every date parameter takes plain English: `today`, `yesterday`, `7 days ago`, `last 30 days`, `this week`, `last month`, `3 months ago`, `2 years ago`, `2026-05`, `2026-05-12`, or full ISO timestamps.

## Connecting each AI

`whoop-mcp setup` handles Claude Desktop and Claude Code automatically. Manual equivalents:

**Claude Desktop** — `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) / `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "whoop": { "command": "/absolute/path/to/whoop-mcp", "args": ["serve"] }
  }
}
```

**Claude Code**

```bash
claude mcp add --scope user whoop -- whoop-mcp serve
```

**ChatGPT** — ChatGPT connects to remote servers, so expose the HTTP transport:

```bash
whoop-mcp serve --transport http --port 8000    # endpoint: /mcp
ngrok http 8000                                  # or any tunnel / small VPS
```

Then **Settings → Apps & Connectors → Advanced settings → Developer mode → create connector** with the tunnel URL + `/mcp`, no auth. The server implements the `search`/`fetch` contract, so it also works with plain connectors and Deep Research.

> ⚠️ A no-auth tunnel means anyone with the URL can read your health data. Keep the URL private and the tunnel short-lived. Claude's stdio setup never exposes anything.

**Anything else** — MCP Inspector: `npx @modelcontextprotocol/inspector whoop-mcp serve`

## Why this is the one to use

- **Exhaustive.** Every read endpoint in WHOOP API v2, including the relational cycle→recovery/sleep lookups and the granular sleep sensor stream most integrations don't know exist. `include_raw` and `export_data` guarantee you can always get the untouched payloads.
- **Trend math that's actually right.** WHOOP returns records newest-first; naive integrations regress over arrival order and report every trend backwards. Series here are sorted by date, and directions respect polarity — rising HRV is *improving*, rising resting HR is *declining*.
- **Timezone-correct days.** Records are bucketed onto calendar days using each record's own timezone offset. Your sleep belongs to the morning you woke up — even when you travel.
- **OAuth that survives reality.** WHOOP rotates *both* tokens on every refresh. Refreshes here are lock-serialized and persisted before use; concurrent requests share one rotation; a re-auth rescues a live server without restart; a failed disk write doesn't lose the rotated pair.
- **A polite API citizen.** Honors `X-RateLimit-Reset`, retries 5xx with jittered backoff, paginates with caps, caches briefly, and tells you when a result was truncated instead of pretending it's complete.
- **Built for LLMs.** Milliseconds → `"7h 37m"`, kilojoules → calories, HR zones → minutes + percentages; structured content on every tool; analysis is computed server-side so the model never does arithmetic on 90 raw JSON records.
- **Tested like it matters.** 91 tests including live in-process MCP sessions against a faked WHOOP API, token-rotation race tests, and timezone edge cases. CI on Python 3.10–3.13.

**A note for WHOOP Peak members:** everything WHOOP's public API exposes is covered here. A few app-only features (stress monitor, healthspan/WHOOP Age) have no public API endpoints yet — the moment WHOOP ships them, they'll land here.

## CLI

```text
whoop-mcp setup     Guided setup: app → authorize → auto-configure clients (start here)
whoop-mcp serve     Run the server (--transport stdio|http|sse, --host, --port)
whoop-mcp auth      Just the OAuth flow (scriptable: --client-id/--client-secret/--no-browser)
whoop-mcp status    Show config, token expiry, scopes
whoop-mcp doctor    Diagnose python/sdk/credentials/connectivity, with fixes
whoop-mcp logout    Delete local tokens (--revoke also revokes at WHOOP)
```

## Configuration

Zero configuration needed after `whoop-mcp setup`. Overrides, in priority order — process env, `./.env`, `~/.whoop-mcp/.env`, `~/.whoop-mcp/config.json`:

| Variable | Default | Purpose |
| --- | --- | --- |
| `WHOOP_CLIENT_ID` / `WHOOP_CLIENT_SECRET` | — | WHOOP app credentials |
| `WHOOP_REDIRECT_URI` | `http://localhost:8765/callback` | Must exactly match the dashboard |
| `WHOOP_MCP_DIR` | `~/.whoop-mcp` | Tokens, config, and exports live here |
| `WHOOP_MCP_TZ` | system zone | IANA timezone for "today", week bounds |
| `WHOOP_MCP_CACHE_TTL` | `60` | Seconds to cache collection responses |
| `WHOOP_MCP_TIMEOUT` | `30` | Per-request timeout (seconds) |
| `WHOOP_MCP_LOG_LEVEL` | `INFO` | Logging (stderr only; stdout belongs to MCP) |
| `WHOOP_ACCESS_TOKEN` | — | Static-token escape hatch (testing; no refresh) |

## Privacy & security

- All data tools are read-only and annotated as such; the only writes are local (`export_data` to your disk) and the OAuth flow you trigger.
- Tokens and credentials live locally with `0600` permissions. No telemetry, no third-party services; the only network peer is `api.prod.whoop.com`.
- Aggregates (trends, correlations, anomalies) can reveal more than single records. Connect this only to AI clients you trust with your health data.

## Development

```bash
uv venv && uv pip install -e ".[dev]"
pytest && ruff check .
```

`client.py` (httpx: auth, retries, rate limits, pagination, cache) → `transform.py` (raw → clean shapes) → `summaries.py` / `analytics.py` (day bucketing, trends, correlations, records) → `server.py` (FastMCP tools/resources/prompts). `oauth.py` + `tokens.py` own the auth lifecycle; `export.py` the bulk exporter; `clients.py` the Claude auto-config; `cli.py` the human surface.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| "WHOOP authorization required" | `whoop-mcp setup` — or ask your AI to connect your WHOOP account |
| Browser opens but redirect fails | Dashboard redirect URI must be exactly `http://localhost:8765/callback`; port 8765 free |
| `403 forbidden — missing scope` | Enable all read scopes on the app, re-run `whoop-mcp auth` |
| Tools missing in Claude Desktop | Re-run `whoop-mcp setup` (it fixes the config), then fully quit and reopen Claude |
| Today shows no recovery | WHOOP scores recovery after you wake and sync; the summary says so |
| Sleep stream "not available" | WHOOP doesn't expose the stream endpoint for every account/app — nightly summaries still work |
| Anything else | `whoop-mcp doctor`, or `get_connection_status` from inside the chat |

## License

MIT — see [LICENSE](LICENSE).

*Not affiliated with or endorsed by WHOOP. WHOOP is a trademark of WHOOP, Inc.*
