import time
from collections import defaultdict
from fastapi import HTTPException, Request, status
from typing import Dict

class RateLimiter:
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, key: str, max_requests: int = 5, window: int = 720) -> bool:
        """5 requêtes par 12 minutes par défaut"""
        now = time.time()
        # Nettoyer les anciennes requêtes
        self.requests[key] = [req_time for req_time in self.requests[key] if now - req_time < window]
        
        if len(self.requests[key]) >= max_requests:
            return False
        
        self.requests[key].append(now)
        return True

rate_limiter = RateLimiter()

def rate_limit_login(request: Request):
    client_ip = request.client.host
    if not rate_limiter.is_allowed(f"login:{client_ip}", max_requests=5, window=720):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop de tentatives de connexion. Réessayez dans 12 minutes."
        )
    return True