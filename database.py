import os
from dotenv import load_dotenv
import libsql_experimental as libsql
import asyncio

# Load environment variables from .env
load_dotenv()

# Create the connection

# Updated function to execute queries asynchronously
async def execute_query(query: str, params: tuple = ()):
    conn = libsql.connect(os.getenv("TURSO_DATABASE_URL"), auth_token=os.getenv("TURSO_AUTH_TOKEN"))
    try:
        result = conn.execute(query, params)
        return result.fetchall()
    except Exception as e:
        print(f"Database error: {e}")
        raise
