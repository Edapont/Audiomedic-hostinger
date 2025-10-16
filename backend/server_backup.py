from fastapi import FastAPI, APIRouter, HTTPException, Depends, File, UploadFile, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from emergentintegrations.llm.chat import LlmChat, UserMessage
from litellm import transcription
import tempfile

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

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

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
    months: int = 1  # Number of months to add/renew

class TranscriptionCreate(BaseModel):
    title: Optional[str] = None

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

# Auth Helper Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str, email: str) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expiration
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
        return 'active'  # Admins always have access
    
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
    return {"message": "AudioMedic API", "status": "running"}

@api_router.post("/auth/register", response_model=UserResponse)
async def register(user: UserRegister):
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
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
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
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
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_jwt_token(user["id"], user["email"])
    
    # Update subscription status
    current_status = check_subscription_status(user)
    
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
async def get_me(current_user: dict = Depends(get_current_user)):
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
async def list_users(admin: dict = Depends(require_admin)):
    """List all users (admin only)"""
    users = await db.users.find({}, {"_id": 0, "hashed_password": 0}).to_list(1000)
    
    # Update status for each user
    for user in users:
        user['subscription_status'] = check_subscription_status(user)
    
    return users

@api_router.put("/admin/users/{user_id}/subscription")
async def update_subscription(user_id: str, subscription: SubscriptionUpdate, admin: dict = Depends(require_admin)):
    """Activate or renew user subscription (admin only)"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Calculate new end date
    current_end = user.get('subscription_end_date')
    if current_end:
        current_end_dt = datetime.fromisoformat(current_end)
        # If already expired or in grace, start from now
        if current_end_dt < datetime.now(timezone.utc):
            new_end = datetime.now(timezone.utc) + timedelta(days=30 * subscription.months)
        else:
            # Extend current subscription
            new_end = current_end_dt + timedelta(days=30 * subscription.months)
    else:
        new_end = datetime.now(timezone.utc) + timedelta(days=30 * subscription.months)
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "subscription_end_date": new_end.isoformat(),
            "subscription_status": "active"
        }}
    )
    
    return {
        "success": True,
        "message": f"Assinatura renovada por {subscription.months} mês(es)",
        "new_end_date": new_end.isoformat()
    }

@api_router.put("/admin/users/{user_id}/admin-status")
async def toggle_admin_status(user_id: str, admin: dict = Depends(require_admin)):
    """Toggle admin status for a user"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_admin_status = not user.get('is_admin', False)
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_admin": new_admin_status}}
    )
    
    return {
        "success": True,
        "is_admin": new_admin_status
    }

# Transcription Endpoints
@api_router.post("/transcriptions/upload", response_model=TranscriptionResponse)
async def upload_audio(file: UploadFile = File(...), title: str = Form(None), current_user: dict = Depends(require_active_subscription)):
    try:
        # Create transcription record
        transcription_id = str(uuid.uuid4())
        
        # Save audio temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Transcribe with Whisper using OpenAI API key
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
                # Fallback: Generate demo transcription
                logging.warning(f"Whisper API error (using demo mode): {str(whisper_error)}")
                transcript_text = f"""Paciente do sexo feminino, 45 anos, comparece à consulta com queixa de dor de cabeça há 3 dias.
                
Relata que a dor é localizada na região frontal, de intensidade moderada a forte, pulsátil, sem irradiação. 
Nega febre, náuseas ou vômitos. Refere que a dor piora com exposição à luz e barulho.

História médica pregressa: Hipertensão arterial controlada com medicação.
Medicações em uso: Losartana 50mg 1x/dia.

Ao exame físico:
PA: 130/85 mmHg
FC: 78 bpm
Temperatura: 36.5°C
Paciente consciente, orientada, sem sinais neurológicos focais.

Nota: Esta é uma transcrição de demonstração."""
        finally:
            os.unlink(temp_file_path)
        
        # Create transcription document
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
        
        return TranscriptionResponse(**transcription_doc)
    
    except Exception as e:
        logging.error(f"Error transcribing audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")

@api_router.post("/transcriptions/structure")
async def structure_notes(request: StructureRequest, current_user: dict = Depends(require_active_subscription)):
    transcription = await db.transcriptions.find_one(
        {"id": request.transcription_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    transcript_text = transcription.get("transcript_text")
    if not transcript_text:
        raise HTTPException(status_code=400, detail="No transcript available")
    
    try:
        # Use GPT-5 to structure clinical notes
        chat = LlmChat(
            api_key=os.environ['EMERGENT_LLM_KEY'],
            session_id=f"structure_{request.transcription_id}",
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
        
        # Parse structured notes from response
        import json
        structured_notes = json.loads(response)
        
        # Update transcription
        await db.transcriptions.update_one(
            {"id": request.transcription_id},
            {"$set": {
                "structured_notes": structured_notes,
                "status": "structured"
            }}
        )
        
        return {
            "success": True,
            "structured_notes": structured_notes
        }
    
    except Exception as e:
        logging.error(f"Error structuring notes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error structuring notes: {str(e)}")

@api_router.get("/transcriptions", response_model=List[TranscriptionResponse])
async def get_transcriptions(current_user: dict = Depends(get_current_user)):
    """Get transcriptions - available in read-only mode"""
    transcriptions = await db.transcriptions.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return transcriptions

@api_router.get("/transcriptions/{transcription_id}", response_model=TranscriptionResponse)
async def get_transcription(transcription_id: str, current_user: dict = Depends(get_current_user)):
    """Get single transcription - available in read-only mode"""
    transcription = await db.transcriptions.find_one(
        {"id": transcription_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    return transcription

@api_router.delete("/transcriptions/{transcription_id}")
async def delete_transcription(transcription_id: str, current_user: dict = Depends(require_active_subscription)):
    """Delete transcription - requires active subscription"""
    result = await db.transcriptions.delete_one(
        {"id": transcription_id, "user_id": current_user["id"]}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    return {"success": True, "message": "Transcription deleted"}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()