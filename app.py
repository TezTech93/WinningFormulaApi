from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import Metrics.routes as metrics_router
import Sports.routes as sports_router
import Users.routes as users_router
import logging

app = FastAPI()

app.include_router(users_router.router) #users
app.include_router(sports_router.router) #sports
app.include_router(metrics_router.router) #metrics

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your React Native app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"message": "Winners Formula Api working!"}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)