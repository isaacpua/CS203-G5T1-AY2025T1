# Load .env before importing routes because the routes file needs it
from dotenv import load_dotenv
load_dotenv()

import warnings
from fastapi import FastAPI
from routes import router

from fastapi.middleware.cors import CORSMiddleware  

warnings.filterwarnings('ignore')

app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,     # Allow specific origins
    allow_credentials=True,    # Allow cookies
    allow_methods=["*"],       # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],       # Allow all headers
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8090)
