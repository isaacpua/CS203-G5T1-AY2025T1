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
    "https://tarific.rocks",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
