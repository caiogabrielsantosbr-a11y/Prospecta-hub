"""
Authentication middleware for FastAPI
Validates Supabase JWT tokens and extracts user information
"""
import os
import logging
from typing import Optional
from fastapi import HTTPException, Header, status
from jose import jwt, JWTError, ExpiredSignatureError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SUPABASE_JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET', '')


def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract and validate user ID from Supabase JWT token.
    
    Args:
        authorization: Authorization header with Bearer token
        
    Returns:
        str: User ID (UUID) from the token
        
    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    
    # Validate token
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=['HS256'],
            options={"verify_aud": False},
        )

        user_id = payload.get('sub')
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
            )

        logger.debug(f"Authenticated user: {user_id}")
        return user_id

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        logger.error(f"Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """
    Extract user ID from token if present, otherwise return None.
    Used for endpoints that work with or without authentication.
    
    Args:
        authorization: Authorization header with Bearer token
        
    Returns:
        Optional[str]: User ID if token is valid, None otherwise
    """
    if not authorization:
        return None
    
    try:
        return get_current_user(authorization)
    except HTTPException:
        return None
