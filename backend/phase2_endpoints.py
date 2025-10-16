"""
Additional endpoints for Phase 2:
- Email verification
- Password reset
- Password change
- MFA/TOTP setup for admins
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address
import secrets
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import logging

# These will be imported from main server.py
# from server import db, get_current_user, require_admin, limiter
# from security_utils import hash_password, is_password_strong, sanitize_email
# from email_utils import send_verification_email, send_password_reset_email, send_mfa_setup_email

logger = logging.getLogger(__name__)

# Models
class RequestPasswordReset(BaseModel):
    email: EmailStr
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        from security_utils import sanitize_email
        return sanitize_email(v)

class ResetPassword(BaseModel):
    token: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        from security_utils import is_password_strong
        is_valid, error_msg = is_password_strong(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v

class ChangePassword(BaseModel):
    current_password: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        from security_utils import is_password_strong
        is_valid, error_msg = is_password_strong(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v

class VerifyEmail(BaseModel):
    token: str

class SetupMFAResponse(BaseModel):
    secret: str
    qr_code: str
    backup_codes: List[str]

class VerifyMFA(BaseModel):
    code: str

class ValidateMFALogin(BaseModel):
    email: EmailStr
    password: str
    mfa_code: str


# Helper Functions
def generate_token(length: int = 32) -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(length)

def generate_backup_codes(count: int = 10) -> List[str]:
    """Generate backup codes for MFA"""
    return [secrets.token_hex(4).upper() for _ in range(count)]

def generate_qr_code(secret: str, email: str) -> str:
    """Generate QR code for TOTP setup"""
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name="AudioMedic"
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{qr_base64}"

def verify_totp_code(secret: str, code: str) -> bool:
    """Verify TOTP code"""
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


# Route definitions (to be added to main server.py)
PHASE2_ROUTES = """
# ============================================================================
# PHASE 2: Email Verification + Password Reset + MFA
# ============================================================================

# Email Verification Endpoints
@api_router.post("/auth/resend-verification")
@limiter.limit("3/hour")
async def resend_verification_email(request: Request, current_user: dict = Depends(get_current_user)):
    '''Resend email verification link'''
    if current_user.get('email_verified', False):
        raise HTTPException(status_code=400, detail="Email já verificado")
    
    # Generate new verification token
    token = generate_token()
    token_expiry = datetime.now(timezone.utc) + timedelta(hours=24)
    
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {
            "verification_token": token,
            "verification_token_expiry": token_expiry.isoformat()
        }}
    )
    
    # Send email
    from email_utils import send_verification_email
    await send_verification_email(current_user["email"], token, current_user["name"])
    
    logging.info(f"Verification email resent to {current_user['email']}")
    
    return {"success": True, "message": "Email de verificação enviado"}

@api_router.post("/auth/verify-email")
@limiter.limit("10/minute")
async def verify_email(verify: VerifyEmail, request: Request):
    '''Verify email with token'''
    user = await db.users.find_one({
        "verification_token": verify.token
    })
    
    if not user:
        raise HTTPException(status_code=400, detail="Token inválido")
    
    # Check if token expired
    token_expiry = user.get('verification_token_expiry')
    if token_expiry:
        expiry_dt = datetime.fromisoformat(token_expiry)
        if datetime.now(timezone.utc) > expiry_dt:
            raise HTTPException(status_code=400, detail="Token expirado. Solicite um novo.")
    
    # Verify email
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "email_verified": True,
            "verification_token": None,
            "verification_token_expiry": None,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    logging.info(f"Email verified for user {user['email']}")
    
    return {"success": True, "message": "Email verificado com sucesso"}

# Password Reset Endpoints
@api_router.post("/auth/request-password-reset")
@limiter.limit("3/hour")
async def request_password_reset(reset_request: RequestPasswordReset, request: Request):
    '''Request password reset link'''
    user = await db.users.find_one({"email": reset_request.email})
    
    # Always return success to prevent email enumeration
    if not user:
        logging.warning(f"Password reset requested for non-existent email: {reset_request.email}")
        return {"success": True, "message": "Se o email existir, um link de recuperação foi enviado"}
    
    # Generate reset token
    token = generate_token()
    token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "reset_token": token,
            "reset_token_expiry": token_expiry.isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Send email
    from email_utils import send_password_reset_email
    await send_password_reset_email(user["email"], token, user["name"])
    
    logging.info(f"Password reset requested for {user['email']}")
    
    return {"success": True, "message": "Se o email existir, um link de recuperação foi enviado"}

@api_router.post("/auth/reset-password")
@limiter.limit("5/hour")
async def reset_password(reset: ResetPassword, request: Request):
    '''Reset password with token'''
    user = await db.users.find_one({
        "reset_token": reset.token
    })
    
    if not user:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")
    
    # Check if token expired
    token_expiry = user.get('reset_token_expiry')
    if token_expiry:
        expiry_dt = datetime.fromisoformat(token_expiry)
        if datetime.now(timezone.utc) > expiry_dt:
            raise HTTPException(status_code=400, detail="Token expirado. Solicite um novo link")
    
    # Hash new password
    from security_utils import hash_password
    hashed_password = hash_password(reset.new_password)
    
    # Update password and clear reset token
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "hashed_password": hashed_password,
            "reset_token": None,
            "reset_token_expiry": None,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    logging.info(f"Password reset completed for {user['email']}")
    
    return {"success": True, "message": "Senha redefinida com sucesso"}

# Password Change (when logged in)
@api_router.post("/auth/change-password")
@limiter.limit("5/hour")
async def change_password(change: ChangePassword, request: Request, current_user: dict = Depends(get_current_user)):
    '''Change password when logged in'''
    from security_utils import verify_password, hash_password
    
    # Verify current password
    if not verify_password(change.current_password, current_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Senha atual incorreta")
    
    # Hash new password
    hashed_password = hash_password(change.new_password)
    
    # Update password
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {
            "hashed_password": hashed_password,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    logging.info(f"Password changed for {current_user['email']}")
    
    return {"success": True, "message": "Senha alterada com sucesso"}

# MFA/TOTP Endpoints (Admin only)
@api_router.post("/auth/setup-mfa", response_model=SetupMFAResponse)
@limiter.limit("5/hour")
async def setup_mfa(request: Request, current_user: dict = Depends(require_admin)):
    '''Setup MFA/TOTP for admin user'''
    # Generate TOTP secret
    secret = pyotp.random_base32()
    
    # Generate QR code
    qr_code = generate_qr_code(secret, current_user["email"])
    
    # Generate backup codes
    backup_codes = generate_backup_codes(10)
    
    # Store secret and backup codes (not yet confirmed)
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {
            "mfa_secret_pending": secret,
            "mfa_backup_codes": backup_codes,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    logging.info(f"MFA setup initiated for admin {current_user['email']}")
    
    return SetupMFAResponse(
        secret=secret,
        qr_code=qr_code,
        backup_codes=backup_codes
    )

@api_router.post("/auth/confirm-mfa")
@limiter.limit("10/minute")
async def confirm_mfa(verify: VerifyMFA, request: Request, current_user: dict = Depends(require_admin)):
    '''Confirm MFA setup with verification code'''
    secret = current_user.get('mfa_secret_pending')
    
    if not secret:
        raise HTTPException(status_code=400, detail="MFA não foi configurado. Execute /auth/setup-mfa primeiro")
    
    # Verify code
    if not verify_totp_code(secret, verify.code):
        raise HTTPException(status_code=400, detail="Código inválido")
    
    # Activate MFA
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {
            "mfa_enabled": True,
            "mfa_secret": secret,
            "mfa_secret_pending": None,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Send confirmation email
    from email_utils import send_mfa_setup_email
    await send_mfa_setup_email(current_user["email"], current_user["name"])
    
    logging.info(f"MFA confirmed and activated for admin {current_user['email']}")
    
    return {"success": True, "message": "MFA ativado com sucesso"}

@api_router.post("/auth/disable-mfa")
@limiter.limit("5/hour")
async def disable_mfa(verify: VerifyMFA, request: Request, current_user: dict = Depends(require_admin)):
    '''Disable MFA (requires code verification)'''
    if not current_user.get('mfa_enabled', False):
        raise HTTPException(status_code=400, detail="MFA não está ativado")
    
    secret = current_user.get('mfa_secret')
    backup_codes = current_user.get('mfa_backup_codes', [])
    
    # Verify code or backup code
    is_valid = verify_totp_code(secret, verify.code) or verify.code.upper() in backup_codes
    
    if not is_valid:
        raise HTTPException(status_code=400, detail="Código inválido")
    
    # Disable MFA
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {
            "mfa_enabled": False,
            "mfa_secret": None,
            "mfa_backup_codes": [],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    logging.info(f"MFA disabled for admin {current_user['email']}")
    
    return {"success": True, "message": "MFA desativado"}

@api_router.get("/auth/mfa-status")
@limiter.limit("30/minute")
async def get_mfa_status(request: Request, current_user: dict = Depends(get_current_user)):
    '''Check if MFA is enabled for current user'''
    return {
        "mfa_enabled": current_user.get('mfa_enabled', False),
        "mfa_required": current_user.get('is_admin', False),  # Required for admins
        "backup_codes_count": len(current_user.get('mfa_backup_codes', []))
    }

# Modified login to support MFA
# Note: This replaces the existing login endpoint
@api_router.post("/auth/login-with-mfa")
@limiter.limit("10/minute")
async def login_with_mfa(credentials: ValidateMFALogin, request: Request):
    '''Login with MFA support'''
    from security_utils import verify_password, reset_login_attempts
    from security_utils import is_account_locked, record_failed_login, get_remaining_attempts
    
    email = credentials.email
    
    # Check if account is locked
    is_locked, locked_until = is_account_locked(email)
    if is_locked:
        minutes_remaining = int((locked_until - datetime.now(timezone.utc)).total_seconds() / 60)
        raise HTTPException(
            status_code=429,
            detail=f"Conta bloqueada por {minutes_remaining} minutos"
        )
    
    # Find user
    user = await db.users.find_one({"email": email})
    
    # Validate credentials
    if not user or not verify_password(credentials.password, user["hashed_password"]):
        record_failed_login(email)
        remaining = get_remaining_attempts(email)
        raise HTTPException(status_code=401, detail=f"Credenciais inválidas. {remaining} tentativas restantes")
    
    # Check if MFA is enabled
    if user.get('mfa_enabled', False):
        secret = user.get('mfa_secret')
        backup_codes = user.get('mfa_backup_codes', [])
        
        # Verify MFA code
        is_valid = verify_totp_code(secret, credentials.mfa_code) or credentials.mfa_code.upper() in backup_codes
        
        if not is_valid:
            record_failed_login(email)
            raise HTTPException(status_code=401, detail="Código MFA inválido")
        
        # Remove backup code if used
        if credentials.mfa_code.upper() in backup_codes:
            backup_codes.remove(credentials.mfa_code.upper())
            await db.users.update_one(
                {"id": user["id"]},
                {"$set": {"mfa_backup_codes": backup_codes}}
            )
    
    # Reset failed attempts
    reset_login_attempts(email)
    
    # Create token
    from server import create_jwt_token
    token = create_jwt_token(user["id"], user["email"])
    
    # Update last login
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
    )
    
    from server import check_subscription_status
    current_status = check_subscription_status(user)
    
    logging.info(f"User logged in with MFA: {email}")
    
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "subscription_status": current_status,
            "subscription_end_date": user.get("subscription_end_date"),
            "is_admin": user.get("is_admin", False)
        }
    }
"""
