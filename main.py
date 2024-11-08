from fastapi import FastAPI
from routes.csg_routes import csg_routes
from routes.formatter_routes import formatter_router
from api_endpoints import db_router

app = FastAPI()

# Include the existing CSG routes
app.include_router(csg_routes, prefix="/api")

# Include the new database routes
app.include_router(db_router, prefix="/api/db")

# Include the new formatter routes
app.include_router(formatter_router, prefix="/api/formatter")