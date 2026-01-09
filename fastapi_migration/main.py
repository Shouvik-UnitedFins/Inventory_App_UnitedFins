from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, users, products, inventory, vendors
from database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)
vendor.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="UnitedFins Inventory Management API",
    description="A comprehensive inventory management system with role-based authentication",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])
app.include_router(vendors.router, prefix="/vendors", tags=["Vendors"])

@app.get("/", tags=["Root"])
async def root():
    return {"message": "UnitedFins Inventory Management API", "version": "1.0.0"}

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}