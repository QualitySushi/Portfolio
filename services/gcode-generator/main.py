from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import generation

app = FastAPI(
    title="G-Code Generator API",
    description="Backend microservice handling geometry processing and generation factory patterns.",
    version="1.0.0"
)

# Configure CORS (allowing requests routed through Express Gateway or direct local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(generation.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}