# Load .env before importing routes because the routes file needs it
from dotenv import load_dotenv
load_dotenv()

import warnings
from fastapi import FastAPI
from routes import router

warnings.filterwarnings('ignore')

app = FastAPI()

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8090,
        workers=4
    )
