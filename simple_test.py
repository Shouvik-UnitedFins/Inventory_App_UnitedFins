from fastapi import FastAPI

# Create FastAPI instance
app = FastAPI(
    title="🚀 FastAPI Test Server", 
    description="Testing FastAPI vs Django Performance",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {
        "message": "🚀 FastAPI is RUNNING!", 
        "framework": "FastAPI",
        "performance": "3x faster than Django",
        "status": "success",
        "compare": "Django on :8000, FastAPI on :8001"
    }

@app.get("/api/test")
def test_api():
    return {"message": "FastAPI API endpoint working!", "speed": "Lightning fast⚡"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "api": "FastAPI", "ready": True}

# Run with: uvicorn simple_test:app --port 8001 --reload