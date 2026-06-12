# whoop-mcp-server: stdio MCP server for WHOOP data.
#
# Build:  docker build -t whoop-mcp-server .
# Try it: docker run -i --rm -e WHOOP_MCP_DEMO=1 whoop-mcp-server
# Real:   mount your data dir so tokens persist across runs:
#         docker run -i --rm -v ~/.whoop-mcp:/root/.whoop-mcp whoop-mcp-server
#
# Note: the interactive OAuth flow needs a browser, so authorize on the host
# with `whoop-mcp-server setup` first and mount the data dir, or pass
# WHOOP_ACCESS_TOKEN.

FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install --no-cache-dir .

ENTRYPOINT ["whoop-mcp-server"]
CMD ["serve"]
