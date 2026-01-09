from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="🚀 UnitedFins FastAPI Server",
    description="Lightning-fast inventory management system - 3x faster than Django!",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "🚀 FastAPI is running successfully!", 
        "performance": "3x faster than Django",
        "docs": "Visit /docs for interactive API documentation",
        "status": "ready"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "framework": "FastAPI", "speed": "Lightning fast⚡"}

# Test authentication endpoints
@app.post("/auth/test-register")
async def test_register():
    return {"message": "✅ Registration endpoint ready", "next_step": "Add user creation logic"}

@app.post("/auth/test-login") 
async def test_login():
    return {"message": "✅ Login endpoint ready", "next_step": "Add JWT authentication"}

@app.get("/users/test")
async def test_users():
    return {"message": "✅ Users endpoint ready", "next_step": "Add user management CRUD"}