from fastapi import FastAPI
from contextlib import asynccontextmanager
from greeting_mcp_server import mcp as greeting_server
from url_scraper.server import mcp as url_scraper_server
#since we not using qap for dex
# from qap.server import mcp as qap_server
from data_analysis.server import mcp as data_analysis_server
from desktop_automation.server import mcp as desktop_automation_server
# from pptx_generator.server import mcp as pptx_mcp_server
# from present_pptx.server import mcp as present_pptx_server

greet_app = greeting_server.http_app()
url_scraper_app = url_scraper_server.http_app()
# qap_app = qap_server.http_app()
data_analysis_app = data_analysis_server.http_app()
desktop_automation_app = desktop_automation_server.http_app()
# pptx_app = pptx_mcp_server.http_app()
# present_pptx_app = present_pptx_server.http_app()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with greet_app.lifespan(app), url_scraper_app.lifespan(app), data_analysis_app.lifespan(app), desktop_automation_app.lifespan(app):
        yield

app = FastAPI(lifespan=lifespan)
app.mount("/greet", greet_app)
app.mount("/scraper", url_scraper_app)
# app.mount("/qap", qap_app)
app.mount("/data_analysis", data_analysis_app)
app.mount("/desktop_automation", desktop_automation_app)
# app.mount("/pptx", pptx_app)
# app.mount("/present_pptx", present_pptx_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
