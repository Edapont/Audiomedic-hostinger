"""
Security Tests for AudioMedic API
Tests password validation, rate limiting, brute force protection, etc.
"""
import pytest
from security_utils import (
    validate_password_strength,
    is_password_strong,
    hash_password,
    verify_password,
    sanitize_email,
    sanitize_name,
    validate_email_format,
    record_failed_login,
    is_account_locked,
    reset_login_attempts,
    get_remaining_attempts
)

class TestPasswordValidation:
    """Test password strength validation"""
    
    def test_strong_password(self):
        """Test that a strong password passes validation"""
        password = "SecurePass123!@#"
        is_valid, _ = is_password_strong(password)
        assert is_valid is True
    
    def test_weak_password_no_uppercase(self):
        """Test password without uppercase fails"""
        password = "weakpass123!"
        is_valid, error = is_password_strong(password)
        assert is_valid is False
        assert "maiúscula" in error.lower()
    
    def test_weak_password_no_lowercase(self):
        """Test password without lowercase fails"""
        password = "WEAKPASS123!"
        is_valid, error = is_password_strong(password)
        assert is_valid is False
        assert "minúscula" in error.lower()
    
    def test_weak_password_no_digit(self):
        """Test password without digit fails"""
        password = "WeakPassword!"
        is_valid, error = is_password_strong(password)
        assert is_valid is False
        assert "número" in error.lower()
    
    def test_weak_password_no_special(self):
        """Test password without special character fails"""
        password = "WeakPassword123"
        is_valid, error = is_password_strong(password)
        assert is_valid is False
        assert "especial" in error.lower()
    
    def test_weak_password_too_short(self):
        """Test password too short fails"""
        password = "Weak1!"
        is_valid, error = is_password_strong(password)
        assert is_valid is False
        assert "caracteres" in error.lower()
    
    def test_password_validation_details(self):
        """Test detailed password validation"""
        password = "SecurePass123!"
        validations = validate_password_strength(password)
        assert validations["length"] is True
        assert validations["uppercase"] is True
        assert validations["lowercase"] is True
        assert validations["digit"] is True
        assert validations["special"] is True

class TestPasswordHashing:
    """Test password hashing and verification"""
    
    def test_hash_and_verify(self):
        """Test password hashing and verification"""
        password = "TestPassword123!"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
    
    def test_wrong_password(self):
        """Test that wrong password fails verification"""
        password = "TestPassword123!"
        wrong = "WrongPassword123!"
        hashed = hash_password(password)
        assert verify_password(wrong, hashed) is False
    
    def test_hash_uniqueness(self):
        """Test that same password produces different hashes (due to salt)"""
        password = "TestPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

class TestInputSanitization:
    """Test input sanitization"""
    
    def test_sanitize_email(self):
        """Test email sanitization"""
        assert sanitize_email("  TEST@EMAIL.COM  ") == "test@email.com"
        assert sanitize_email("User@Example.Com") == "user@example.com"
    
    def test_sanitize_name(self):
        """Test name sanitization"""
        assert sanitize_name("  John   Doe  ") == "John Doe"
        assert sanitize_name("John\nDoe") == "John Doe"
    
    def test_validate_email_format(self):
        """Test email format validation"""
        assert validate_email_format("user@example.com") is True
        assert validate_email_format("user.name@example.co.uk") is True
        assert validate_email_format("invalid-email") is False
        assert validate_email_format("@example.com") is False
        assert validate_email_format("user@") is False

class TestBruteForceProtection:
    """Test brute force protection"""
    
    def setup_method(self):
        """Reset before each test"""
        from security_utils import login_attempts
        login_attempts.clear()
    
    def test_failed_login_tracking(self):
        """Test that failed logins are tracked"""
        email = "test@example.com"
        
        # Record 3 failed attempts
        for _ in range(3):
            record_failed_login(email)
        
        remaining = get_remaining_attempts(email)
        assert remaining == 2  # MAX_ATTEMPTS=5, so 5-3=2
    
    def test_account_lockout(self):
        """Test that account gets locked after max attempts"""
        email = "test@example.com"
        
        # Record 5 failed attempts
        for _ in range(5):
            record_failed_login(email)
        
        is_locked, locked_until = is_account_locked(email)
        assert is_locked is True
        assert locked_until is not None
    
    def test_reset_attempts(self):
        """Test that successful login resets attempts"""
        email = "test@example.com"
        
        # Record some failed attempts
        record_failed_login(email)
        record_failed_login(email)
        
        # Reset after successful login
        reset_login_attempts(email)
        
        remaining = get_remaining_attempts(email)
        assert remaining == 5  # Back to max
    
    def test_lockout_prevents_more_attempts(self):
        """Test that locked account doesn't increment attempts"""
        email = "test@example.com"
        
        # Lock the account
        for _ in range(5):
            record_failed_login(email)
        
        # Try to record more attempts
        record_failed_login(email)
        record_failed_login(email)
        
        # Should still be at 5 attempts
        remaining = get_remaining_attempts(email)
        assert remaining == 0

class TestSecurityHeaders:
    """Test security headers middleware"""
    
    def test_security_headers_present(self):
        """Test that security headers are set"""
        from security_middleware import SecurityHeadersMiddleware
        from starlette.middleware.base import BaseHTTPMiddleware
        
        assert issubclass(SecurityHeadersMiddleware, BaseHTTPMiddleware)

def run_tests():
    """Run all security tests"""
    pytest.main([__file__, "-v", "--tb=short"])

if __name__ == "__main__":
    run_tests()
