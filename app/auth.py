import os
from fastapi import Header, HTTPException

API_KEY = os.environ["API_KEY"]
API_KEY_SYSTEM = os.environ["API_KEY_SYSTEM"]

valid_apis = [API_KEY, API_KEY_SYSTEM]

async def require_api_key(x_api_key: str = Header(...)):
    if x_api_key not in valid_apis:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_api_key