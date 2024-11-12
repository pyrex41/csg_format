import httpx
from typing import Dict, Optional

def lookup_routing_number(routing_number: str) -> Dict:
    """
    Look up bank name for a routing number using routingnumbers.info API.
    
    Args:
        routing_number: The routing number to look up
        
    Returns:
        Dict containing response code, message and bank name if found
    """
    if not routing_number:
        return {
            "code": 400,
            "message": "Routing number is required"
        }
        
    try:
        with httpx.Client() as client:
            response = client.get(
                f"https://www.routingnumbers.info/api/name.json",
                params={"rn": routing_number}
            )
            data = response.json()
            
            if data.get("code") == 200:
                return {
                    "code": 200,
                    "message": "OK",
                    "rn": routing_number,
                    "name": data.get("name")
                }
            else:
                return {
                    "code": 404, 
                    "message": "Bank not found"
                }
                
    except Exception as e:
        print(f"Error looking up routing number: {str(e)}")
        return {
            "code": 500,
            "message": "Error looking up bank name"
        }
