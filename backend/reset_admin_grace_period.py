#!/usr/bin/env python3
"""
Gerar QR Code e habilitar MFA para admin sem período de graça expirado
SOLUÇÃO ALTERNATIVA: Atualizar data de criação do admin para hoje
"""
import asyncio
import os
import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def reset_admin_date():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("═══════════════════════════════════════════════════════════════")
    print("   Solução Temporária: Reset Data Admin (Ganhar 7 dias)")
    print("═══════════════════════════════════════════════════════════════\n")
    
    # Find admins without MFA
    admins = await db.users.find(
        {"is_admin": True, "mfa_enabled": {"$ne": True}},
        {"_id": 0, "id": 1, "email": 1, "created_at": 1}
    ).to_list(10)
    
    if not admins:
        print("✅ Todos os admins já têm MFA configurado ou não há admins.")
        client.close()
        return
    
    print("Admins encontrados sem MFA:\n")
    for i, admin in enumerate(admins, 1):
        print(f"{i}. {admin['email']} (criado em: {admin.get('created_at', 'N/A')[:10]})")
    
    print("\n⚠️  ATENÇÃO:")
    print("Esta ação vai resetar a data de criação dos admins para HOJE,")
    print("dando a eles 7 dias de período de graça para configurar MFA.\n")
    print("Esta é uma solução TEMPORÁRIA. O ideal é configurar MFA.")
    print("\n═══════════════════════════════════════════════════════════════\n")
    
    # Reset all admins without MFA
    now = datetime.now(timezone.utc).isoformat()
    
    for admin in admins:
        result = await db.users.update_one(
            {"id": admin['id']},
            {"$set": {"created_at": now, "updated_at": now}}
        )
        
        if result.modified_count > 0:
            print(f"✅ {admin['email']} - Data resetada para hoje")
        else:
            print(f"❌ {admin['email']} - Falha ao resetar")
    
    print("\n═══════════════════════════════════════════════════════════════")
    print("✅ Período de graça reativado!")
    print("═══════════════════════════════════════════════════════════════\n")
    print("Agora você tem 7 dias para:")
    print("  1. Renovar assinaturas de usuários")
    print("  2. Configurar MFA via interface web (/auth/setup-mfa)")
    print("\n⏰ Após 7 dias, o MFA será OBRIGATÓRIO novamente.")
    print("═══════════════════════════════════════════════════════════════\n")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(reset_admin_date())
