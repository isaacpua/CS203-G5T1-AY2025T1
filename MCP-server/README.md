```
python3 -m venv .venv
```

```
source .venv/bin/activate
```

```
pip install -r requirements.txt
```

```
fastapi run
```



# MCP Backend Servers

This repository hosts a collection of backend servers built using the FastMCP framework. Each server is designed as a modular, self-contained unit that exposes a set of related tools. The initial server provided is the `url_scraper`, a powerful service for web scraping with advanced features like paywall detection and bypass.

## Project Philosophy

The goal of this project is to create a clear, scalable, and maintainable architecture for deploying multiple MCP servers. Each server should reside in its own directory and be independently runnable, but share a common structural pattern. This ensures that as the project grows, it remains organized and easy for developers to navigate.

## Directory Structure

The project is organized to keep each server and its related components isolated. This makes it easy to work on a single server without affecting others. Here is the standard structure for any server within this repository, using `url_scraper` as the example:

```
mcp_backend_dev/
│
├── url_scraper/
│   ├── server.py             # Main server file: Defines tools and runs the FastMCP server.
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── scrape_url.py       # Core logic for scraping a URL.
│   │   ├── detect_paywall.py   # Logic for detecting paywalls.
│   │   ├── open_login_browser.py # Logic for handling interactive logins.
│   │   └── utils.py            # Shared helper functions for the url_scraper tools.
│   │
│   └── tests/
│       └── e2e_agent_test.py   # End-to-end test client/agent for the server.
│
├── .gitignore
└── README.md
```

### Key Components:

- **`server.py`**: The entry point for the server. It uses `@mcp.tool` decorators to expose functions from the `tools` directory as callable endpoints. It is responsible for defining the server's public API.
- **`tools/`**: This directory contains the core business logic for the server's tools. Each file should encapsulate a specific piece of functionality. Complex logic is broken down into smaller, more manageable functions.
- **`tools/utils.py`**: A dedicated module for helper functions that are shared across multiple tools within the _same server_. This promotes code reuse and keeps the main tool files clean.
- **`tests/`**: Contains tests for the server. The `e2e_agent_test.py` is a perfect example of a client that consumes the server's tools to perform a complex workflow.

---

## Setup and Installation

To get the project running, you'll need to set up a Python environment and install the required dependencies.

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd mcp_backend_dev
    ```

2.  **Create a virtual environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:** All required packages are listed in `requirements.txt`.

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:** The `url_scraper` server uses the OpenAI API for its vision-based paywall detection. Create a `.env` file in the project root:
    ```
    touch .env
    ```
    And add your OpenAI API key to it:
    ```.env
    OPENAI_API_KEY="sk-..."
    ```

---

## How to Run

You need to run the server first, and then you can run the test client in a separate terminal to interact with it.

### 1. Run the URL Scraper Server

The server provides the tools for scraping.

```bash
# In your first terminal window, from the project root:
python url_scraper/server.py
```

You should see output indicating the server has started, running on port `8080`:

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

### 2. Run the Test Agent (Client)

The test agent simulates a user or another application using the server's tools to perform the end-to-end paywall bypass workflow.

```bash
# In a second terminal window, from the project root:
python url_scraper/tests/e2e_agent_test.py
```

The script will prompt you to enter a URL. Provide a URL (e.g., a paywalled news article or Medium post) and watch the agent work. It will:

1.  Call the `detect_paywall` tool.
2.  If a paywall is found, call `open_login_browser`, which will open a browser window for you to log in.
3.  After you close the browser, it will call `scrape_single_url` to get the full content.

---

## `url_scraper` Server Tools

The server exposes the following tools at the `/scraper/` endpoint:

| Tool                 | Description                                                                                                                                                               |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `scrape_single_url`  | The main scraping tool. It renders JavaScript, handles authenticated sessions, and uses vision analysis to intelligently extract the main content from a URL as Markdown. |
| `detect_paywall`     | Quickly checks if a URL has a paywall by using a combination of keyword detection and GPT-4o vision analysis on a screenshot of the page.                                 |
| `open_login_browser` | Opens a visible browser window for the user to manually log in or solve a CAPTCHA. It saves the resulting session state for use in subsequent authenticated scrapes.      |

---

## Guide for Future Developers

To add a new server to this project (e.g., `document_processor`), follow the established structure:

1.  **Create the Server Directory:**

    ```bash
    mkdir document_processor
    ```

2.  **Follow the Standard Layout:** Inside `document_processor/`, create the standard file structure:

    ```
    document_processor/
    ├── server.py
    ├── tools/
    │   ├── __init__.py
    │   └── ... (your tool logic files)
    └── tests/
        └── ... (your test files)
    ```

3.  **Implement Your Logic:**
    - Write your core functions in the `document_processor/tools/` directory.
    - In `document_processor/server.py`, import your functions and expose them as tools using the `@mcp.tool()` decorator.
    - Create a test client in `document_processor/tests/` to validate your server's functionality.

By adhering to this modular structure, we can ensure the project remains clean, scalable, and easy to maintain.

## Desktop Automation notes

- Implement concurrency in the future by using a dictionary to contain different ms graph clients for different users
