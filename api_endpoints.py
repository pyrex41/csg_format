from fastapi import APIRouter, Depends, HTTPException
from database import execute_query

db_router = APIRouter()


# Create router@db_router.get("/users")
def read_users():
    return [dict(user) for user in execute_query("SELECT * FROM user")]

@db_router.post("/users")
def create_user(user_id: str, email: str, isTemporary: bool, isAnonymous: bool):
    execute_query(
        "INSERT INTO user (id, email, isTemporary, isAnonymous) VALUES (?, ?, ?, ?)",
        (user_id, email, isTemporary, isAnonymous)
    )
    return {"message": "User created"}

@db_router.get("/users/{user_id}")
def get_user(user_id: str):
    user = execute_query("SELECT * FROM user WHERE id = ?", (user_id,))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(user[0])


@db_router.get("/applications")
def read_applications():
    return [dict(app) for app in execute_query("SELECT * FROM applications")]

@db_router.get("/applications/{application_id}")
async def get_application(application_id: str):
    application = await execute_query("SELECT * FROM applications WHERE id = ?", (application_id,))
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return list(application[0])

@db_router.post("/applications")
def create_application(
    application_id: str,
    user_id: str,
    status: str,
    data: dict,
    zip_code: str,
    county: str,
    dob: str,
    schema: dict,
    original_schema: dict,
    underwriting_type: int = 0,
    name: str = None,
    naic: str = None,
):
    execute_query(
        """INSERT INTO applications 
           (id, userId, status, data, name, naic, zip, county, dob, schema, originalSchema, underwritingType) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (application_id, user_id, status, data, name, naic, zip_code, county, dob, schema, original_schema, underwriting_type)
    )
    return {"message": "Application created"}
