import warnings
from contextlib import asynccontextmanager
from fastapi import FastAPI
from routes import router
warnings.filterwarnings('ignore')

app = FastAPI()

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8090)
