from fastmcp import FastMCP
from pydantic import Field
from fastapi import Request
from fastapi.responses import JSONResponse

mcp = FastMCP(
    name="DexiaMCP",
    instructions="""
        This server provides greet tools.
        Call greet() to greet someone.
    """,
)

# --- Healthcheck Route ---
@mcp.custom_route("/", methods=["GET"])
async def healthcheck(request: Request) -> JSONResponse:
    """
    Responds with a 200 OK status for health checks, required by Cloud Run.
    """
    return JSONResponse({"status": "ok"})

@mcp.tool(
    name="greet",
    description="Greets the user with a personalized message.",
)
async def greet(name: str = Field(..., description="The name of the user to greet.")) -> str:
    return f"Hello abc {name}!"

@mcp.tool(
    name="prepareGreeting",
    description="Prepare a greeting for the user. This is a tool that is used to prepare a greeting for the user. You MUST call this tool before calling the greet tool.",
)
async def prepareGreeting() -> str:
    return f"Greeting prepared!"


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=4200,
        path="/mcp",
        log_level="debug",
    )
