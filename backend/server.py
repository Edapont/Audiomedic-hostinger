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
    created_at: str

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
    
    user_doc = {
        "id": user_id,
        "email": user.email,
        "name": user.name,
        "hashed_password": hashed_pw,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
    return UserResponse(
        id=user_id,
        email=user.email,
        name=user.name,
        created_at=user_doc["created_at"]
    )

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_jwt_token(user["id"], user["email"])
    
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"]
        }
    }

# Transcription Endpoints
@api_router.post("/transcriptions/upload", response_model=TranscriptionResponse)
async def upload_audio(file: UploadFile = File(...), title: str = Form(None), current_user: dict = Depends(get_current_user)):
    try:
        # Create transcription record
        transcription_id = str(uuid.uuid4())
        
        # Save audio temporarily for Whisper API
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Transcribe with Whisper
            with open(temp_file_path, 'rb') as audio_file:
                transcript = await openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="pt"
                )
            
            transcript_text = transcript.text
        finally:
            # Delete temporary file
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
async def structure_notes(request: StructureRequest, current_user: dict = Depends(get_current_user)):
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
    transcriptions = await db.transcriptions.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return transcriptions

@api_router.get("/transcriptions/{transcription_id}", response_model=TranscriptionResponse)
async def get_transcription(transcription_id: str, current_user: dict = Depends(get_current_user)):
    transcription = await db.transcriptions.find_one(
        {"id": transcription_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    return transcription

@api_router.delete("/transcriptions/{transcription_id}")
async def delete_transcription(transcription_id: str, current_user: dict = Depends(get_current_user)):
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