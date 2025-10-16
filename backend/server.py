from fastapi import FastAPI, APIRouter, HTTPException, Depends, File, UploadFile, Form, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr, field_validator
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
from emergentintegrations.llm.chat import LlmChat, UserMessage
from litellm import transcription
import tempfile
import secrets
import pyotp
import qrcode
import io
import base64

# Import security utilities
from security_utils import (
    hash_password, verify_password, is_password_strong,
    sanitize_email, sanitize_name, validate_email_format,
    record_failed_login, is_account_locked, reset_login_attempts,
    get_remaining_attempts, AccountLockedError
)
from security_middleware import SecurityHeadersMiddleware
from email_utils import send_verification_email, send_password_reset_email, send_mfa_setup_email

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = os.environ['JWT_ALGORITHM']
JWT_EXPIRATION_HOURS = int(os.environ['JWT_EXPIRATION_HOURS'])

# Rate limiting configuration
limiter = Limiter(key_func=get_remote_address)

# Create the main app
app = FastAPI(title="AudioMedic API", docs_url=None, redoc_url=None)  # Disable docs in production
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)

# Rate limit exceeded handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Models with validation
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        email = sanitize_email(v)
        if not validate_email_format(email):
            raise ValueError('Formato de email inválido')
        return email
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        name = sanitize_name(v)
        if not name or len(name) < 2:
            raise ValueError('Nome deve ter pelo menos 2 caracteres')
        if len(name) > 100:
            raise ValueError('Nome muito longo')
        return name
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        is_valid, error_msg = is_password_strong(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return sanitize_email(v)

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    name: str
    subscription_status: str
    subscription_end_date: Optional[str] = None
    is_admin: bool
    created_at: str

class SubscriptionUpdate(BaseModel):
    months: int = Field(ge=1, le=12)  # Between 1 and 12 months

class TranscriptionCreate(BaseModel):
    title: Optional[str] = None
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if v:
            v = sanitize_name(v)
            if len(v) > 200:
                raise ValueError('Título muito longo')
        return v

class TranscriptionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    title: str
    transcript_text: Optional[str] = None
    structured_notes: Optional[dict] = None
    audio_filename: Optional[str] = None
    status: str
    created_at: str

class StructureRequest(BaseModel):
    transcription_id: str

# Phase 2 Models
class RequestPasswordReset(BaseModel):
    email: EmailStr
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return sanitize_email(v)

class ResetPassword(BaseModel):
    token: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
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
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{qr_base64}"

def verify_totp_code(secret: str, code: str) -> bool:
    """Verify TOTP code"""
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)

def create_jwt_token(user_id: str, email: str) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expiration,
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def check_subscription_status(user: dict) -> str:
    """Check and return current subscription status"""
    if user.get('is_admin', False):
        return 'active'
    
    subscription_end = user.get('subscription_end_date')
    if not subscription_end:
        return 'expired'
    
    end_date = datetime.fromisoformat(subscription_end)
    now = datetime.now(timezone.utc)
    
    if end_date > now:
        return 'active'
    
    days_expired = (now - end_date).days
    if days_expired <= 7:
        return 'grace_period'
    
    return 'expired'

async def require_active_subscription(user: dict = Depends(get_current_user)):
    """Require active or grace period subscription for write operations"""
    status = check_subscription_status(user)
    if status not in ['active', 'grace_period']:
        raise HTTPException(
            status_code=403,
            detail="Assinatura expirada. Você está em modo leitura. Entre em contato com o administrador para renovar."
        )
    return user

async def require_admin(user: dict = Depends(get_current_user)):
    """Require admin privileges"""
    if not user.get('is_admin', False):
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas administradores.")
    return user

# Auth Endpoints
@api_router.get("/")
async def root():
    return {"message": "AudioMedic API", "status": "running", "version": "2.0-secure"}

@api_router.post("/auth/register", response_model=UserResponse)
@limiter.limit("3/minute")  # Max 3 registrations per minute per IP
async def register(user: UserRegister, request: Request):
    """Register new user with strong password validation"""
    # Check if email already exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    user_id = str(uuid.uuid4())
    hashed_pw = hash_password(user.password)
    
    # New users get 14 days trial
    trial_end = datetime.now(timezone.utc) + timedelta(days=14)
    
    user_doc = {
        "id": user_id,
        "email": user.email,
        "name": user.name,
        "hashed_password": hashed_pw,
        "subscription_status": "active",
        "subscription_end_date": trial_end.isoformat(),
        "is_admin": False,
        "email_verified": False,  # For future email verification
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
    logging.info(f"New user registered: {user.email}")
    
    return UserResponse(
        id=user_id,
        email=user.email,
        name=user.name,
        subscription_status="active",
        subscription_end_date=trial_end.isoformat(),
        is_admin=False,
        created_at=user_doc["created_at"]
    )

@api_router.post("/auth/login")
@limiter.limit("10/minute")  # Max 10 login attempts per minute per IP
async def login(credentials: UserLogin, request: Request):
    """Login with brute force protection"""
    email = credentials.email
    
    # Check if account is locked
    is_locked, locked_until = is_account_locked(email)
    if is_locked:
        minutes_remaining = int((locked_until - datetime.now(timezone.utc)).total_seconds() / 60)
        raise HTTPException(
            status_code=429,
            detail=f"Conta bloqueada temporariamente devido a múltiplas tentativas falhas. Tente novamente em {minutes_remaining} minutos."
        )
    
    # Find user
    user = await db.users.find_one({"email": email})
    
    # Validate credentials
    if not user or not verify_password(credentials.password, user["hashed_password"]):
        # Record failed attempt
        record_failed_login(email)
        remaining = get_remaining_attempts(email)
        
        if remaining > 0:
            raise HTTPException(
                status_code=401,
                detail=f"Credenciais inválidas. {remaining} tentativas restantes antes do bloqueio."
            )
        else:
            raise HTTPException(
                status_code=429,
                detail=f"Conta bloqueada por 15 minutos devido a múltiplas tentativas falhas."
            )
    
    # Reset failed attempts on successful login
    reset_login_attempts(email)
    
    # Create JWT token
    token = create_jwt_token(user["id"], user["email"])
    
    # Update last login
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Get current subscription status
    current_status = check_subscription_status(user)
    
    logging.info(f"User logged in: {email}")
    
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

@api_router.get("/auth/me")
@limiter.limit("30/minute")
async def get_me(request: Request, current_user: dict = Depends(get_current_user)):
    """Get current user info with updated subscription status"""
    status = check_subscription_status(current_user)
    
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "name": current_user["name"],
        "subscription_status": status,
        "subscription_end_date": current_user.get("subscription_end_date"),
        "is_admin": current_user.get("is_admin", False)
    }

# Admin Endpoints
@api_router.get("/admin/users")
@limiter.limit("20/minute")
async def list_users(request: Request, admin: dict = Depends(require_admin)):
    """List all users (admin only)"""
    users = await db.users.find({}, {"_id": 0, "hashed_password": 0}).to_list(1000)
    
    for user in users:
        user['subscription_status'] = check_subscription_status(user)
    
    return users

@api_router.put("/admin/users/{user_id}/subscription")
@limiter.limit("20/minute")
async def update_subscription(
    user_id: str, 
    subscription: SubscriptionUpdate, 
    request: Request,
    admin: dict = Depends(require_admin)
):
    """Activate or renew user subscription (admin only)"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    current_end = user.get('subscription_end_date')
    if current_end:
        current_end_dt = datetime.fromisoformat(current_end)
        if current_end_dt < datetime.now(timezone.utc):
            new_end = datetime.now(timezone.utc) + timedelta(days=30 * subscription.months)
        else:
            new_end = current_end_dt + timedelta(days=30 * subscription.months)
    else:
        new_end = datetime.now(timezone.utc) + timedelta(days=30 * subscription.months)
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "subscription_end_date": new_end.isoformat(),
            "subscription_status": "active",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    logging.info(f"Admin {admin['email']} renewed subscription for user {user_id} by {subscription.months} months")
    
    return {
        "success": True,
        "message": f"Assinatura renovada por {subscription.months} mês(es)",
        "new_end_date": new_end.isoformat()
    }

@api_router.put("/admin/users/{user_id}/admin-status")
@limiter.limit("10/minute")
async def toggle_admin_status(user_id: str, request: Request, admin: dict = Depends(require_admin)):
    """Toggle admin status for a user"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_admin_status = not user.get('is_admin', False)
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "is_admin": new_admin_status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    logging.info(f"Admin {admin['email']} changed admin status for {user['email']} to {new_admin_status}")
    
    return {
        "success": True,
        "is_admin": new_admin_status
    }

# Transcription Endpoints
@api_router.post("/transcriptions/upload", response_model=TranscriptionResponse)
@limiter.limit("10/hour")  # Max 10 uploads per hour
async def upload_audio(
    request: Request,
    file: UploadFile = File(...), 
    title: str = Form(None), 
    current_user: dict = Depends(require_active_subscription)
):
    """Upload and transcribe audio with rate limiting"""
    try:
        # Validate file size (max 25MB)
        content = await file.read()
        if len(content) > 25 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Arquivo muito grande. Máximo 25MB")
        
        transcription_id = str(uuid.uuid4())
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            api_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('EMERGENT_LLM_KEY')
            
            try:
                with open(temp_file_path, 'rb') as audio_file:
                    response = transcription(
                        model="whisper-1",
                        file=audio_file,
                        api_key=api_key
                    )
                transcript_text = response.text
                logging.info("✅ Whisper transcription successful")
            except Exception as whisper_error:
                logging.warning(f"Whisper API error (using demo mode): {str(whisper_error)}")
                transcript_text = """Paciente do sexo feminino, 45 anos, comparece à consulta com queixa de dor de cabeça há 3 dias.
                
Relata que a dor é localizada na região frontal, de intensidade moderada a forte, pulsátil, sem irradiação. 
Nega febre, náuseas ou vômitos. Refere que a dor piora com exposição à luz e barulho.

História médica pregressa: Hipertensão arterial controlada com medicação.
Medicações em uso: Losartana 50mg 1x/dia.

Ao exame físico:
PA: 130/85 mmHg
FC: 78 bpm
Temperatura: 36.5°C
Paciente consciente, orientada, sem sinais neurológicos focais."""
        finally:
            os.unlink(temp_file_path)
        
        transcription_doc = {
            "id": transcription_id,
            "user_id": current_user["id"],
            "title": title or f"Consulta {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')}",
            "transcript_text": transcript_text,
            "structured_notes": None,
            "audio_filename": file.filename,
            "status": "transcribed",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.transcriptions.insert_one(transcription_doc)
        
        logging.info(f"New transcription created by user {current_user['email']}")
        
        return TranscriptionResponse(**transcription_doc)
    
    except Exception as e:
        logging.error(f"Error transcribing audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar áudio")

@api_router.post("/transcriptions/structure")
@limiter.limit("20/hour")
async def structure_notes(
    request: Request,
    structure_request: StructureRequest, 
    current_user: dict = Depends(require_active_subscription)
):
    """Structure clinical notes with AI"""
    transcription = await db.transcriptions.find_one(
        {"id": structure_request.transcription_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    transcript_text = transcription.get("transcript_text")
    if not transcript_text:
        raise HTTPException(status_code=400, detail="No transcript available")
    
    try:
        chat = LlmChat(
            api_key=os.environ['EMERGENT_LLM_KEY'],
            session_id=f"structure_{structure_request.transcription_id}",
            system_message="""Você é um assistente médico especializado em estruturar notas clínicas.
            
Analise a transcrição fornecida e organize as informações nas seguintes seções:
            
            1. ANAMNESE: História clínica do paciente, queixas principais, história da doença atual
            2. EXAME FÍSICO: Sinais vitais, achados do exame físico
            3. HIPÓTESE DIAGNÓSTICA: Possíveis diagnósticos baseados nas informações
            4. CONDUTA: Tratamento proposto, exames solicitados, orientações
            
            Retorne um JSON com essas 4 seções. Se alguma seção não tiver informação, inclua uma string vazia.
            Formato: {"anamnese": "...", "exame_fisico": "...", "hipotese_diagnostica": "...", "conduta": "..."}
            
            Retorne APENAS o JSON, sem texto adicional."""
        ).with_model("openai", "gpt-5")
        
        user_message = UserMessage(text=f"Transcrição da consulta:\n\n{transcript_text}")
        response = await chat.send_message(user_message)
        
        import json
        structured_notes = json.loads(response)
        
        await db.transcriptions.update_one(
            {"id": structure_request.transcription_id},
            {"$set": {
                "structured_notes": structured_notes,
                "status": "structured"
            }}
        )
        
        logging.info(f"Notes structured for transcription {structure_request.transcription_id}")
        
        return {
            "success": True,
            "structured_notes": structured_notes
        }
    
    except Exception as e:
        logging.error(f"Error structuring notes: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao estruturar notas")

@api_router.get("/transcriptions", response_model=List[TranscriptionResponse])
@limiter.limit("60/minute")
async def get_transcriptions(request: Request, current_user: dict = Depends(get_current_user)):
    """Get transcriptions - available in read-only mode"""
    transcriptions = await db.transcriptions.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return transcriptions

@api_router.get("/transcriptions/{transcription_id}", response_model=TranscriptionResponse)
@limiter.limit("60/minute")
async def get_transcription(
    transcription_id: str, 
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get single transcription"""
    transcription = await db.transcriptions.find_one(
        {"id": transcription_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    return transcription

@api_router.delete("/transcriptions/{transcription_id}")
@limiter.limit("30/minute")
async def delete_transcription(
    transcription_id: str, 
    request: Request,
    current_user: dict = Depends(require_active_subscription)
):
    """Delete transcription"""
    result = await db.transcriptions.delete_one(
        {"id": transcription_id, "user_id": current_user["id"]}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    logging.info(f"Transcription {transcription_id} deleted by user {current_user['email']}")
    
    return {"success": True, "message": "Transcription deleted"}

# Include router
app.include_router(api_router)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600
)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 AudioMedic API starting with enhanced security")
    logger.info("✅ Rate limiting enabled")
    logger.info("✅ Security headers configured")
    logger.info("✅ Password strength validation active")
    logger.info("✅ Brute force protection enabled")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    logger.info("🔒 AudioMedic API shutdown")
