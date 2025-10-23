# dexnew_backend

This project is a FastAPI backend server that provides various services, including scraping, presentation generation, and other helpful utilities.

---

## Prerequisites

Before you begin, ensure you have the following installed:

-   **Python 3.10.18**

---

## Setup and Installation

Follow these steps to set up the project and install the necessary dependencies.

1.  **Create a virtual environment:**

    ```bash
    python -m venv .venv
    ```

2.  **Activate the virtual environment:**

    -   On **macOS and Linux**:
        ```bash
        source .venv/bin/activate
        ```
    -   On **Windows**:
        ```bash
        .venv\Scripts\activate
        ```

3.  **Install the required packages:**

    ```bash
    pip install -r requirements.txt
    ```

---

## Running the Development Server

Once the setup is complete, you can start the development server.

1.  **Navigate to the `src` directory:**

    ```bash
    cd src
    ```

2.  **Start the FastAPI server:**

    ```bash
    fastapi dev app.py --port 8001
    ```

The server will be running at `http://127.0.0.1:8001`, and the API documentation can be accessed at `http://127.0.0.1:8001/docs`.
This is because frontend is hardcoded to connect to port 8001


## Available Tools
Tools will be pulled from https://github.com/DrLukeTan/mcp_backend_dev


