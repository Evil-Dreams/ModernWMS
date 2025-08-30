import logging
import json
import base64
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Dict, Tuple, Optional, Any
from jose import jwt, JWTError

from .config import JWT_SECRET, JWT_ISSUER, JWT_AUDIENCE

logger = logging.getLogger(__name__)

class TokenCache:
    """
    A thread-safe token cache that handles both refresh tokens and access tokens.
    Implements token storage, validation, and rotation.
    """
    
    def __init__(self):
        # Structure: {user_id: {"refresh_token": str, "expires_at": datetime, "metadata": dict}}
        self._refresh_tokens: Dict[int, Dict[str, Any]] = {}
        # Structure: {token: {"user_id": int, "expires_at": datetime}}
        self._token_lookup: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        
    def set_token(self, user_id: int, token: str, expires_delta: timedelta) -> None:
        """
        Store a refresh token for a user.
        
        Args:
            user_id: The ID of the user
            token: The refresh token string
            expires_delta: Time until the token expires
        """
        expires_at = datetime.now(timezone.utc) + expires_delta
        
        with self._lock:
            # Invalidate any existing token for this user
            self._invalidate_user_tokens(user_id)
            
            # Store the new token
            self._refresh_tokens[user_id] = {
                "refresh_token": token,
                "expires_at": expires_at,
                "metadata": {"created_at": datetime.now(timezone.utc)}
            }
            self._token_lookup[token] = {
                "user_id": user_id,
                "expires_at": expires_at
            }
            
        logger.debug(f"Set refresh token for user {user_id} expiring at {expires_at}")
    
    def get_user_id_by_token(self, token: str) -> Optional[int]:
        """
        Get the user ID associated with a refresh token.
        
        Args:
            token: The refresh token to look up
            
        Returns:
            int: The user ID if the token is valid, None otherwise
        """
        with self._lock:
            token_info = self._token_lookup.get(token)
            if not token_info:
                return None
                
            # Check if token is expired
            if token_info["expires_at"] < datetime.now(timezone.utc):
                self._invalidate_token(token)
                return None
                
            return token_info["user_id"]
    
    def verify_token(self, token: str) -> Optional[dict]:
        """
        Verify a JWT token and return its payload if valid.
        
        Args:
            token: The JWT token to verify
            
        Returns:
            dict: The decoded token payload if valid, None otherwise
        """
        try:
            # First verify the JWT signature and standard claims
            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=["HS256"],
                audience=JWT_AUDIENCE,
                issuer=JWT_ISSUER,
                options={"verify_exp": True}
            )
            
            # For refresh tokens, also check our cache
            if payload.get("type") == "refresh":
                user_id = self.get_user_id_by_token(token)
                if not user_id or user_id != int(payload.get("sub", ":").split(":")[-1]):
                    return None
            
            return payload
            
        except JWTError as e:
            logger.warning(f"Token validation failed: {str(e)}")
            return None
    
    def delete_token(self, user_id: int) -> bool:
        """
        Delete a user's refresh token.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            bool: True if a token was deleted, False if no token existed
        """
        with self._lock:
            return self._invalidate_user_tokens(user_id)
    
    def _invalidate_user_tokens(self, user_id: int) -> bool:
        """Internal method to remove all tokens for a user."""
        if user_id not in self._refresh_tokens:
            return False
            
        token = self._refresh_tokens[user_id]["refresh_token"]
        del self._token_lookup[token]
        del self._refresh_tokens[user_id]
        return True
    
    def _invalidate_token(self, token: str) -> bool:
        """Internal method to remove a specific token."""
        if token not in self._token_lookup:
            return False
            
        user_id = self._token_lookup[token]["user_id"]
        if user_id in self._refresh_tokens:
            del self._refresh_tokens[user_id]
        del self._token_lookup[token]
        return True
    
    def cleanup_expired_tokens(self) -> int:
        """
        Remove all expired tokens from the cache.
        
        Returns:
            int: Number of tokens removed
        """
        removed = 0
        now = datetime.now(timezone.utc)
        
        with self._lock:
            # Clean up expired tokens in the lookup
            expired_tokens = [
                token for token, data in self._token_lookup.items()
                if data["expires_at"] < now
            ]
            
            for token in expired_tokens:
                self._invalidate_token(token)
                removed += 1
            
            # Clean up any remaining orphaned user entries
            expired_users = [
                user_id for user_id, data in self._refresh_tokens.items()
                if data["expires_at"] < now
            ]
            
            for user_id in expired_users:
                del self._refresh_tokens[user_id]
                removed += 1
        
        if removed > 0:
            logger.info(f"Cleaned up {removed} expired tokens")
            
        return removed

# Global cache instance
cache = TokenCache()

def get_cache() -> TokenCache:
    """Get the global token cache instance."""
    return cache
