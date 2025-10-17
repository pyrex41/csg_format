from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from routes.csg_routes import csg_routes
from routes.formatter_routes import formatter_router
from routes.auth_routes import auth_router
from api_endpoints import db_router

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routes (no auth required for login)
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])

# Include the existing CSG routes
app.include_router(csg_routes, prefix="/api", tags=["csg"])

# Include the new database routes
app.include_router(db_router, prefix="/api/db", tags=["database"])

# Include the new formatter routes
app.include_router(formatter_router, prefix="/api/formatter", tags=["formatter"])

# Mount static files directory for the front-end interface
app.mount("/", StaticFiles(directory="static", html=True), name="static")

