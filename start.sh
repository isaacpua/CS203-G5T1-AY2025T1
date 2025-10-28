#!/bin/sh

# This spring boot doesn't shut down gracefully, it is commented out
# (cd tariff-backend && ./mvnw spring-boot:run) &
(cd tariff-frontend && npm run dev) &
# (cd MCP-Server && uv run main.py) &
(cd MCP-Server && .venv/bin/python3 -m main) &
# (cd MCP-Gateway && uv run main.py)
(cd MCP-Gateway && .venv/bin/python3 -m main)
&& kill $!
