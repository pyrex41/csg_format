import jwt
import requests
from datetime import datetime, timedelta
import os
# Replace with actual formatting logic
def format_application(application: dict) -> dict:
    application['applicant_info']['full_name'] = f"{application['applicant_info']['f_name']} {application['applicant_info']['l_name']}"
    # Add more formatting based on business rules
    return application

class TokenManager:
    def __init__(self, api_url=os.getenv("CSG_API_URL")):
        self.api_url = api_url
        self.token = None
        self.expires_date = None

    def get_token(self, credentials: dict) -> str:
        """
        Get a valid token, either by using existing one or generating new one
        credentials: dict containing either:
            - email and password
            - api_key
            - email, password, and portal_name (for portal accounts)
        """
        # Check if current token is still valid
        if self.token and self.expires_date and datetime.now() < self.expires_date:
            return self.token

        # Request new token
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            f"{self.api_url}/auth",
            json=credentials,
            headers=headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Authentication failed: {response.text}")

        auth_data = response.json()
        self.token = auth_data.get("token")
        # Convert expires_date string to datetime
        self.expires_date = datetime.fromisoformat(auth_data.get("expires_date"))
        
        return self.token

# Create a singleton instance of TokenManager
_token_manager = TokenManager()

def get_token() -> str:
    """
    Global function to get a token using environment variables for credentials
    Returns: str - Valid authentication token
    """
    credentials = {
        "email": os.getenv("CSG_EMAIL"),
        "password": os.getenv("CSG_PASSWORD"),
        "api_key": os.getenv("CSG_API_KEY")
    }
    
    # Remove None values
    credentials = {k: v for k, v in credentials.items() if v is not None}
    
    if not credentials:
        raise Exception("No credentials found in environment variables")
        
    return _token_manager.get_token(credentials)

# Example usage:
# token = get_token()
