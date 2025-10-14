# MCP Backend Servers

This repository hosts a collection of backend servers built using the FastMCP framework. Each server is designed as a modular, self-contained unit that exposes a set of related tools. This project provides a scalable and maintainable architecture for deploying multiple MCP servers, including a `url_scraper`, `data_analysis` server, `greeting` server, and a `desktop_automation` server.

## Project Philosophy

The goal of this project is to create a clear, scalable, and maintainable architecture for deploying multiple MCP servers. Each server resides in its own directory and is independently runnable but shares a common structural pattern. This ensures that as the project grows, it remains organized and easy for developers to navigate.

---
## Directory Structure

The project is organized to keep each server and its related components isolated, making it easy to work on a single server without affecting others. Here is the standard structure for any server within this repository:

```
MCP-server
│
├── \<server\_name\>/
│   ├── server.py             \# Main server file: Defines tools and runs the FastMCP server.
│   ├── tools/
│   │   ├── **init**.py
│   │   └── ... (tool logic files)
│   │
│   └── tests/
│       └── ... (test files for the server)
│
├── .gitignore
└── README.md
````

### Key Components:

* **`server.py`**: The entry point for the server. It uses `@mcp.tool` decorators to expose functions from the `tools` directory as callable endpoints and is responsible for defining the server's public API.
* **`tools/`**: This directory contains the core business logic for the server's tools. Each file should encapsulate a specific piece of functionality.
* **`tests/`**: Contains tests for the server.

---

## Setup and Installation

To get the project running, you'll need to set up a Python environment and install the required dependencies.

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd MCP-server
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

4.  **Set up environment variables:** Some servers may require API keys or other environment variables. Create a `.env` file in the project root:
    ```
    touch .env
    ```
    And add any necessary variables, for example:
    ```.env
    OPENAI_API_KEY="sk-..."
    ```

---
## How to Run

To run the MCP server, execute the `main.py` file:

```bash
# In your terminal, from the project root:
fastapi run
````

You should see output indicating the server has started, by default on port `8000`:

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on [http://127.0.0.1:8000](http://127.0.0.1:8000) (Press CTRL+C to quit)
```

-----

## Available Servers

The main application mounts the following servers:

### `/greet`

A simple server for greeting users.

  * **`greet`**: Greets the user with a personalized message.
  * **`prepareGreeting`**: Prepares a greeting for the user.

### `/scraper`

A powerful service for web scraping with advanced features like paywall detection and bypass.

| Tool | Description |
|---|---|
| `scrape_single_url` | Renders JavaScript, handles authenticated sessions, and uses vision analysis to intelligently extract the main content from a URL as Markdown. |
| `detect_paywall` | Quickly checks if a URL has a paywall by using a combination of keyword detection and GPT-4o vision analysis on a screenshot of the page. |
| `open_login_browser` | Opens a visible browser window for the user to manually log in or solve a CAPTCHA. It saves the resulting session state for use in subsequent authenticated scrapes. |

### `/data_analysis`

Provides advanced data analysis tools that operate on user-uploaded datasets.

  * **`run_analysis`**: Analyzes a dataset based on a natural language prompt, supporting:
      * **regression**: Fits and interprets linear regression models.
      * **describe**: Generates descriptive summaries for numerical or categorical columns.
      * **compare**: Runs statistical comparisons between groups (e.g., t-test, ANOVA).
      * **categorical**: Analyzes relationships between categorical variables (e.g., chi-squared, McNemar).
      * **plot**: Generates visualizations based on selected columns.
      * **forecast**: Performs time series forecasting using Prophet.
      * **region analysis**: Analyzes and forecasts spatio-temporal trends across regions.

### `/desktop_automation`

Provides tools for automating desktop tasks and browser automation.

  * **`send_email_without_attachment`**: Sends an email without an attachment.
  * **`send_email_with_attachment`**: Sends an email with an attachment.
  * **`merge_string_with_docx`**: Extracts text from the most recent docx file in the Downloads folder and prepends it with a given string.
  * **`news_headlines_identification`**: Goes to user-provided sites and extracts headlines containing technology-related keywords.

-----

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

      * Write your core functions in the `document_processor/tools/` directory.
      * In `document_processor/server.py`, import your functions and expose them as tools using the `@mcp.tool()` decorator.
      * Create a test client in `document_processor/tests/` to validate your server's functionality.
      * Finally, mount your new server in `main.py`.

By adhering to this modular structure, we can ensure the project remains clean, scalable, and easy to maintain.
