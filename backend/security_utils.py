"""Security utilities for authentication and validation"""
import re
import bcrypt
from typing import Dict, Optional
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import threading

# Password policy constants
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

# Brute force protection
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

# Thread-safe storage for login attempts
login_attempts = defaultdict(lambda: {"count": 0, "locked_until": None})
attempts_lock = threading.Lock()


class PasswordValidationError(Exception):
    """Custom exception for password validation errors"""
    pass


class AccountLockedError(Exception):
    """Custom exception for locked accounts"""
    pass


def validate_password_strength(password: str) -> Dict[str, bool]:
    """
    Validate password against security policy.
    
    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Returns:
        Dict with validation results
    """
    validations = {
        "length": len(password) >= MIN_PASSWORD_LENGTH and len(password) <= MAX_PASSWORD_LENGTH,
        "uppercase": bool(re.search(r'[A-Z]', password)),
        "lowercase": bool(re.search(r'[a-z]', password)),
        "digit": bool(re.search(r'\d', password)),
        "special": bool(re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;\'`~]', password))
    }
    
    return validations


def is_password_strong(password: str) -> tuple[bool, str]:
    """
    Check if password meets all security requirements.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "Senha não pode estar vazia"
    
    validations = validate_password_strength(password)
    
    if not validations["length"]:
        return False, f"Senha deve ter entre {MIN_PASSWORD_LENGTH} e {MAX_PASSWORD_LENGTH} caracteres"
    
    if not validations["uppercase"]:
        return False, "Senha deve conter pelo menos uma letra maiúscula"
    
    if not validations["lowercase"]:
        return False, "Senha deve conter pelo menos uma letra minúscula"
    
    if not validations["digit"]:
        return False, "Senha deve conter pelo menos um número"
    
    if not validations["special"]:
        return False, "Senha deve conter pelo menos um caractere especial (!@#$%^&*...)"
    
    return True, ""


def hash_password(password: str, rounds: int = 12) -> str:
    """
    Hash password using bcrypt with strong cost factor.
    
    Args:
        password: Plain text password
        rounds: Cost factor (default 12 for strong security)
    
    Returns:
        Hashed password string
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=rounds)).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify password against hash.
    
    Args:
        password: Plain text password
        hashed: Hashed password
    
    Returns:
        True if password matches
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def sanitize_email(email: str) -> str:
    """
    Sanitize email address.
    
    Args:
        email: Email address
    
    Returns:
        Sanitized email (lowercase, trimmed)
    """
    return email.strip().lower()


def sanitize_name(name: str) -> str:
    """
    Sanitize user name.
    
    Args:
        name: User name
    
    Returns:
        Sanitized name (trimmed, single spaces)
    """
    # Remove extra whitespace and limit length
    name = ' '.join(name.split())
    return name[:100]  # Max 100 characters


def validate_email_format(email: str) -> bool:
    """
    Validate email format using regex.
    
    Args:
        email: Email address
    
    Returns:
        True if valid format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def record_failed_login(identifier: str) -> None:
    """
    Record a failed login attempt.
    
    Args:
        identifier: User identifier (email or IP)
    """
    with attempts_lock:
        attempts = login_attempts[identifier]
        
        # Check if currently locked
        if attempts["locked_until"] and datetime.now(timezone.utc) < attempts["locked_until"]:
            return  # Still locked, don't increment
        
        # Reset if lock expired
        if attempts["locked_until"] and datetime.now(timezone.utc) >= attempts["locked_until"]:
            attempts["count"] = 0
            attempts["locked_until"] = None
        
        # Increment attempt count
        attempts["count"] += 1
        
        # Lock account if max attempts reached
        if attempts["count"] >= MAX_LOGIN_ATTEMPTS:
            attempts["locked_until"] = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)


def is_account_locked(identifier: str) -> tuple[bool, Optional[datetime]]:
    """
    Check if account is locked due to failed login attempts.
    
    Args:
        identifier: User identifier (email or IP)
    
    Returns:
        Tuple of (is_locked, locked_until_time)
    """
    with attempts_lock:
        attempts = login_attempts[identifier]
        
        if attempts["locked_until"] and datetime.now(timezone.utc) < attempts["locked_until"]:
            return True, attempts["locked_until"]
        
        return False, None


def reset_login_attempts(identifier: str) -> None:
    """
    Reset login attempts after successful login.
    
    Args:
        identifier: User identifier (email or IP)
    """
    with attempts_lock:
        if identifier in login_attempts:
            login_attempts[identifier] = {"count": 0, "locked_until": None}


def get_remaining_attempts(identifier: str) -> int:
    """
    Get remaining login attempts before lockout.
    
    Args:
        identifier: User identifier (email or IP)
    
    Returns:
        Number of remaining attempts
    """
    with attempts_lock:
        attempts = login_attempts[identifier]
        return max(0, MAX_LOGIN_ATTEMPTS - attempts["count"])
