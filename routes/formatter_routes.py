from fastapi import APIRouter, HTTPException
from database import execute_query
from typing import Dict, Any
import json
from datetime import datetime, timezone
from application_formatter import format_application



formatter_router = APIRouter()

async def get_application_by_id(application_id: str) -> Dict[str, Any]:
    """Retrieve application from database by ID."""
    try:
        query = """
        SELECT 
            applications.id, 
            applications.data, 
            applications.naic, 
            applications.schema, 
            applications.original_schema, 
            user.email,
            onboarding.data as onboarding_data
        FROM applications 
        JOIN user ON applications.user_id = user.id 
        LEFT JOIN onboarding ON user.id = onboarding.user_id
        WHERE applications.id = ?
        """
        result = await execute_query(query, (application_id,))
        if not result:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Convert database row to dictionary
        application = {
            "id": result[0][0],
            "data": result[0][1],
            "naic": result[0][2],
            "schema": result[0][3],
            "originalSchema": result[0][4],
            "email": result[0][5],
            "onboarding_data": result[0][6]  # Default value
        }
        
        # Parse JSON fields
        for field in ['data', 'schema', 'originalSchema', 'onboarding_data']:
            if application.get(field):
                application[field] = json.loads(application[field])
        
        return application
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def get_carrier_name(naic: str) -> str:
    """Map NAIC number to carrier name."""
    carrier_map = {
        "79413": "UnitedHealthcare",
        "78700": "Aetna",
        "72052": "Aetna",
        "68500": "Aetna",
        "60380": "Allstate",
        "82538": "Allstate",
        "20699": "Chubb"
    }
    return carrier_map.get(naic, "Unknown")

@formatter_router.get("/api/applications/{application_id}/formatted")
async def get_formatted_application(application_id: str):
    """
    Retrieve and format an application by ID.
    
    Parameters:
    - application_id: The unique identifier of the application
    
    Returns:
    - Formatted application data according to carrier specifications
    """
    try:
        # Get application from database
        application = await get_application_by_id(application_id)
        
        # Get carrier name from NAIC
        carrier = get_carrier_name(application.get('naic'))
        if carrier == "Unknown":
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported NAIC number: {application.get('naic')}"
            )
        
        # Format application
        formatted_data = format_application(application, carrier)
        
        # Replace empty/null string values with "NA" recursively
        def replace_empty_values(obj):
            if isinstance(obj, dict):
                return {k: replace_empty_values(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_empty_values(item) for item in obj]
            elif isinstance(obj, str) and (not obj or obj == "undefined"):
                return "NA"
            elif obj is None:
                return "NA"
            return obj
        
        # Apply the replacement to formatted data
        formatted_data = replace_empty_values(formatted_data)
        
        # Copy all sections from the original data
        if isinstance(application.get("data"), dict):
            for section, content in application["data"].items():
                if section not in formatted_data:
                    formatted_data[section] = replace_empty_values(content)
        
        return {
            "success": True,
            "data": formatted_data,
            "metadata": {
                "application_id": application_id,
                "carrier": carrier,
                "formatted_at": datetime.now(timezone.utc).isoformat(),
                "original_status": application.get('status') or "NA",
                "applicant_email": application.get('email') or "NA"
            }
        }
        
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except ValueError as ve:
        # Handle validation errors
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Error formatting application: {str(e)}"
        )

# Add the router to main.py