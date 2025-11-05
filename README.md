# Installation

- Spring Boot Java version = JDK-17 (as per Intro slides)
- Node 22+ (or at least that's what has been tested to be working so far)

# Development

## React Frontend

```sh
cd tariff-frontend
npm install
npm run dev
```

## Java Springboot Backend

```sh
cd tariff-backend
./mvnw clean spring-boot:run
```

## MCP-Server

### Required Files
- credentials.json — OAuth 2.0 credentials for the email service
- token.json — Generated after first authentication

### macOS/Linux

```sh
cd MCP-Server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# "python3 main.py" works too
fastapi run
```

### Windows

```sh
cd MCP-Server
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
# "python main.py" works too
fastapi run
```

### uv

```sh
cd MCP-Server
uv venv
uv pip install -r requirements.txt
uv run main.py
```

### crawl4ai setup
Within venv, run:
```sh
playwright install
crawl4ai-setup
```

## MCP-Gateway

### macOS/Linux

```sh
cd MCP-Gateway
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

### Windows

```sh
cd MCP-Gateway
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### uv

```sh
cd MCP-Gateway
# "sync" works because MCP-Gateway is a uv project
uv sync
uv run main.py
```

## MCP-client

### macOS/Linux

```sh
cd MCP-client
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_client.py
```

```sh
cd MCP-client
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run_client.py
```
