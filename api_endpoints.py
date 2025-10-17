from fastapi import APIRouter, Depends, HTTPException
from database import execute_query
from auth import get_current_user

db_router = APIRouter()


# Create router@db_router.get("/users")
def read_users(current_user: dict = Depends(get_current_user)):
    return [dict(user) for user in execute_query("SELECT * FROM user")]

@db_router.post("/users")
def create_user(user_id: str, email: str, isTemporary: bool, isAnonymous: bool, current_user: dict = Depends(get_current_user)):
    execute_query(
        "INSERT INTO user (id, email, is_temporary, is_anonymous) VALUES (?, ?, ?, ?)",
        (user_id, email, isTemporary, isAnonymous)
    )
    return {"message": "User created"}

@db_router.get("/users/{user_id}")
def get_user(user_id: str, current_user: dict = Depends(get_current_user)):
    user = execute_query("SELECT * FROM user WHERE id = ?", (user_id,))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(user[0])


@db_router.get("/applications")
async def read_applications(page: int = 1, limit: int = 10, search: str = None, current_user: dict = Depends(get_current_user)):
    """
    Get paginated applications, ordered by most recent first.

    Parameters:
    - page: Page number (starts at 1)
    - limit: Number of items per page (default 10, max 100)
    - search: Optional search term to filter by name, email, zip, county, or ID
    """
    import json

    # Validate and cap the limit
    limit = min(limit, 100)
    offset = (page - 1) * limit

    # Build WHERE clause for search
    where_clause = ""
    search_params = []
    if search:
        where_clause = """WHERE (
            applications.id LIKE ? OR
            applications.zip LIKE ? OR
            applications.county LIKE ? OR
            user.email LIKE ? OR
            applications.data LIKE ?
        )"""
        search_term = f"%{search}%"
        search_params = [search_term] * 5

    # Get total count with search filter
    count_query = f"SELECT COUNT(*) as total FROM applications JOIN user ON applications.user_id = user.id {where_clause}"
    count_result = await execute_query(count_query, tuple(search_params))
    total = count_result[0][0] if count_result else 0

    # Get paginated applications with user email, ordered by created_at DESC
    query = f"""SELECT
           applications.id,
           applications.user_id,
           applications.status,
           applications.created_at,
           applications.updated_at,
           applications.name,
           applications.naic,
           applications.zip,
           applications.county,
           applications.dob,
           applications.underwriting_type,
           applications.data,
           user.email
           FROM applications
           JOIN user ON applications.user_id = user.id
           {where_clause}
           ORDER BY applications.created_at DESC
           LIMIT ? OFFSET ?"""

    applications = await execute_query(query, tuple(search_params + [limit, offset]))

    # Calculate pagination metadata
    total_pages = (total + limit - 1) // limit  # Ceiling division

    # Process applications to extract applicant name from data
    processed_apps = []
    for app in applications:
        app_dict = dict(zip(["id", "userId", "status", "createdAt", "updatedAt", "name", "naic", "zip", "county", "dob", "underwritingType", "data", "email"], app))

        # Extract applicant name from JSON data
        try:
            data = json.loads(app_dict["data"]) if isinstance(app_dict["data"], str) else app_dict["data"]
            applicant_info = data.get("applicant_info", {})
            app_dict["applicantName"] = f"{applicant_info.get('f_name', '')} {applicant_info.get('l_name', '')}".strip()
        except:
            app_dict["applicantName"] = ""

        # Remove the full data field from response to keep it light
        del app_dict["data"]
        processed_apps.append(app_dict)

    return {
        "success": True,
        "data": processed_apps,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

@db_router.get("/applications/{application_id}")
async def get_application(application_id: str, current_user: dict = Depends(get_current_user)):
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
    app_schema: dict,
    app_original_schema: dict,
    underwriting_type: int = 0,
    name: str = None,
    naic: str = None,
    current_user: dict = Depends(get_current_user)
):
    execute_query(
        """INSERT INTO applications
           (id, user_id, status, data, name, naic, zip, county, dob, schema, original_schema, underwriting_type)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (application_id, user_id, status, data, name, naic, zip_code, county, dob, app_schema, app_original_schema, underwriting_type)
    )
    return {"message": "Application created"}
