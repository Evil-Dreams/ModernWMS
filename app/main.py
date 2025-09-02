from fastapi import FastAPI
from .routers import router

app = FastAPI(title="ModernWMS Python Backend")
app.include_router(router)

@app.get("/")
def root():
    return {"message": "Welcome to ModernWMS Python Backend!"}
