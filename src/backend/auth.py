from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import auth, credentials
import os

# Initialize Firebase Admin SDK
# For local dev, we might mock this or need GOOGLE_APPLICATION_CREDENTIALS
# For production (Cloud Run), it auto-detects credentials if not provided explicitly?
# Ideally, user should provide a serviceAccountKey.json path or use default.

try:
    # Check if already initialized to avoid re-init error
    firebase_admin.get_app()
except ValueError:
    # Initialize
    # Ensure you have GOOGLE_APPLICATION_CREDENTIALS set for ADC
    # Or load from specific file: cred = credentials.Certificate("path/to/key.json")
    firebase_admin.initialize_app()

security = HTTPBearer()

async def get_current_user_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validates the Firebase JWT Token.
    """
    token = credentials.credentials
    try:
        # Verify the ID token
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        print(f"Auth Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user_claims(decoded_token: dict = Depends(get_current_user_token)):
    """
    Returns the decoded token claims (uid, email, etc.)
    """
    return decoded_token
