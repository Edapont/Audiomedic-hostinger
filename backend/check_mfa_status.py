import asyncio
import os
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def check():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    admins = await db.users.find({"is_admin": True}, {"_id": 0}).to_list(10)
    
    print("═══════════════════════════════════════════════")
    print("  Status MFA dos Administradores")
    print("═══════════════════════════════════════════════\n")
    
    for admin in admins:
        email = admin['email']
        created_at = admin.get('created_at')
        mfa_enabled = admin.get('mfa_enabled', False)
        
        print(f"👤 {email}")
        print(f"   MFA Ativo: {'✅ Sim' if mfa_enabled else '❌ Não'}")
        
        if created_at:
            created_date = datetime.fromisoformat(created_at)
            days_since_creation = (datetime.now(timezone.utc) - created_date).days
            grace_remaining = max(0, 7 - days_since_creation)
            
            print(f"   Conta criada: {created_at[:10]} ({days_since_creation} dias atrás)")
            
            if not mfa_enabled:
                if grace_remaining > 0:
                    print(f"   ⚠️  Período de graça: {grace_remaining} dias restantes")
                    print(f"   Status: Pode fazer operações críticas (graça)")
                else:
                    print(f"   🚫 Período de graça expirado!")
                    print(f"   Status: BLOQUEADO para operações críticas")
                    print(f"   Solução: Configure MFA para desbloquear")
            else:
                print(f"   ✅ Status: Liberado (MFA ativo)")
        print()
    
    print("═══════════════════════════════════════════════")
    print("Operações Críticas (requerem MFA):")
    print("  - Renovar assinatura de usuários")
    print("  - Alterar status de admin de usuários")
    print("\nOperações Permitidas sem MFA:")
    print("  - Listar usuários")
    print("  - Configurar MFA")
    print("  - Ver status de MFA")
    print("═══════════════════════════════════════════════")
    
    client.close()

asyncio.run(check())
