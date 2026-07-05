from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.routers import chat, admin

app = FastAPI(title="GreenBin Genius AI Coordinator")

app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def read_root():
    return FileResponse("frontend/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
