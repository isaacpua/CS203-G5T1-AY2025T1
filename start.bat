@echo off

REM start them in different terminals
start "tariff-backend" cmd /c "cd tariff-backend && mvnw spring-boot:run"
start "tariff-frontend" cmd /c "cd tariff-frontend && npm run dev"
start "MCP-Server" cmd /c "cd MCP-Server && uv run main.py"
start "MCP-Gateway" cmd /c "cd MCP-Gateway && uv run main.py"
