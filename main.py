from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.database import connect_to_mongo, close_mongo_connection, seed_initial_data
from app.api import goals, tasks, journals, ai, auth, users

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app - Compatible with FastAPI 0.95.2
app = FastAPI(
    title="Swayami API",
    description="Self-Reliance Dashboard - Goal-based productivity companion with AI-powered insights",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    # Custom Swagger UI theming with brand colors
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "displayRequestDuration": True,
        "tryItOutEnabled": True,
        "syntaxHighlight.theme": "arta",
        "layout": "StandaloneLayout",
        "deepLinking": True,
        # Inject custom CSS directly
        "customCss": """
        :root {
            --primary-color: #6FCC7F;
            --primary-hover: #5bb96a;
        }
        .swagger-ui .topbar { 
            background: linear-gradient(135deg, var(--primary-color) 0%, #9650D4 100%);
            border-bottom: 3px solid var(--primary-color);
        }
        .swagger-ui .info .title { color: var(--primary-color); font-weight: 700; }
        .swagger-ui .btn.authorize,
        .swagger-ui .btn.execute { 
            background: var(--primary-color); 
            border-color: var(--primary-color); 
        }
        .swagger-ui .btn.authorize:hover,
        .swagger-ui .btn.execute:hover { 
            background: var(--primary-hover); 
            border-color: var(--primary-hover); 
        }
        .swagger-ui .opblock.opblock-get { border-color: var(--primary-color); }
        .swagger-ui .opblock.opblock-post { border-color: var(--primary-color); }
        .swagger-ui .opblock.opblock-get .opblock-summary-method,
        .swagger-ui .opblock.opblock-post .opblock-summary-method { 
            background: var(--primary-color); 
        }
        """
    }
)

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting Swayami API...")
    try:
        await connect_to_mongo()
        logger.info("✅ Database connection established")
        
        # Seed initial data
        await seed_initial_data()
        logger.info("✅ Initial data seeded")
        
    except Exception as e:
        logger.error(f"❌ Failed to start application: {e}")
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Shutting down Swayami API...")
    await close_mongo_connection()

# CORS middleware with comprehensive configuration for both dev and production
ALLOWED_ORIGINS = [
    # Local development origins
    "http://localhost:3000",
    "http://localhost:3001", 
    "http://localhost:3002",
    "http://localhost:3003",
    "http://localhost:3004",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    # Production/Staging origins
    "https://swayami-focus-mirror.lovable.app",
    "https://swayami-frontend.onrender.com",  # Render staging deployment
    # Production domains
    "https://app.swayami.com",  # Frontend app
    "https://swayami.com",  # Landing page
]

ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
ALLOWED_HEADERS = [
    "Content-Type", 
    "Authorization", 
    "Access-Control-Allow-Origin",
    "Accept",
    "Origin",
    "User-Agent",
    "DNT",
    "Cache-Control",
    "X-Mx-ReqToken",
    "Keep-Alive",
    "X-Requested-With",
    "If-Modified-Since",
]

logger.info("🔧 CORS Configuration:")
logger.info(f"🔧 Allowed Origins: {ALLOWED_ORIGINS}")
logger.info(f"🔧 Allowed Methods: {ALLOWED_METHODS}")
logger.info(f"🔧 Allowed Headers: {ALLOWED_HEADERS}")
logger.info("🔧 Allow Credentials: True")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=ALLOWED_METHODS,
    allow_headers=ALLOWED_HEADERS,
    expose_headers=["*"],  # Allow frontend to access response headers
)

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "🌟 Welcome to Swayami API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs",
        "auth_test": "/api/auth/test"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "swayami-api",
        "database": "connected",
        "auth": "mock_enabled"
    }

# CORS debugging endpoint
@app.get("/cors-test")
async def cors_test():
    """Test endpoint to verify CORS configuration is working"""
    return {
        "message": "✅ CORS is working correctly!",
        "timestamp": "2024-01-01T00:00:00Z",
        "allowed_origins": ALLOWED_ORIGINS,
        "allowed_methods": ALLOWED_METHODS,
        "server": "FastAPI",
        "cors_status": "enabled"
    }

# CORS debugging middleware
@app.middleware("http")
async def cors_debug_middleware(request, call_next):
    origin = request.headers.get("origin")
    method = request.method
    
    # Log CORS-related requests for debugging
    if origin or method == "OPTIONS":
        logger.info(f"🔍 CORS Request - Method: {method}, Origin: {origin}, Path: {request.url.path}")
        
        if origin and origin not in ALLOWED_ORIGINS:
            logger.warning(f"⚠️ CORS Warning - Origin '{origin}' not in allowed origins")
        
        if method == "OPTIONS":
            logger.info("🔧 CORS Preflight request detected")
    
    response = await call_next(request)
    
    # Log CORS response headers for debugging
    if origin or method == "OPTIONS":
        cors_headers = {k: v for k, v in response.headers.items() if "access-control" in k.lower()}
        if cors_headers:
            logger.info(f"🔧 CORS Response Headers: {cors_headers}")
    
    return response

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(goals.router, prefix="/api")
app.include_router(tasks.router, prefix="/api") 
app.include_router(journals.router, prefix="/api")
app.include_router(ai.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 