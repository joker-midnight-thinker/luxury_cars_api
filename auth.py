import os
import base64
import json
import hmac
import hashlib
import time

SECRET_KEY = os.getenv("SECRET_KEY", "redline-motors-premium-secret-key-123456")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 часа

def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def base64url_decode(data: str) -> bytes:
    padding = '=' * (4 - len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

def create_access_token(data: dict, expires_delta_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    expire = int(time.time()) + (expires_delta_minutes * 60)
    to_encode.update({"exp": expire})
    
    header = {"alg": ALGORITHM, "typ": "JWT"}
    
    header_encoded = base64url_encode(json.dumps(header).encode('utf-8'))
    payload_encoded = base64url_encode(json.dumps(to_encode).encode('utf-8'))
    
    signing_input = f"{header_encoded}.{payload_encoded}".encode('utf-8')
    signature = hmac.new(SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
    signature_encoded = base64url_encode(signature)
    
    return f"{header_encoded}.{payload_encoded}.{signature_encoded}"

def verify_token(token: str) -> dict | None:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        header_encoded, payload_encoded, signature_encoded = parts
        signing_input = f"{header_encoded}.{payload_encoded}".encode('utf-8')
        
        expected_signature = hmac.new(SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
        expected_signature_encoded = base64url_encode(expected_signature)
        
        if not hmac.compare_digest(signature_encoded, expected_signature_encoded):
            return None
            
        payload = json.loads(base64url_decode(payload_encoded).decode('utf-8'))
        
        if "exp" in payload and payload["exp"] < int(time.time()):
            return None
            
        return payload
    except Exception:
        return None

def get_password_hash(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return f"pbkdf2_sha256$100000${salt.hex()}${key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        parts = hashed_password.split('$')
        if len(parts) != 4 or parts[0] != 'pbkdf2_sha256':
            return False
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        original_key = bytes.fromhex(parts[3])
        
        new_key = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, iterations)
        return hmac.compare_digest(original_key, new_key)
    except Exception:
        return False
