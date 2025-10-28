import asyncio
import os
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def check():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Find admin users
    admins = await db.users.find({"is_admin": True}, {"_id": 0, "email": 1, "created_at": 1, "mfa_enabled": 1}).to_list(10)
    
    print("Admin users:")
    for admin in admins:
        print(f"  - {admin['email']} (MFA: {admin.get('mfa_enabled', False)}, Created: {admin.get('created_at', 'N/A')[:10]})")
    
    if not admins:
        print("  (No admin users found)")
    
    client.close()

asyncio.run(check())
