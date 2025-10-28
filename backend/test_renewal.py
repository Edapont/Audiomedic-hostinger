import asyncio
import os
import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt

# Load env
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def test_renewal():
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Create test user without subscription
    test_user_id = str(uuid.uuid4())
    hashed_pw = bcrypt.hashpw('TestPassword123!'.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
    
    test_user = {
        "id": test_user_id,
        "email": "testuser@test.com",
        "name": "Test User",
        "hashed_password": hashed_pw,
        "subscription_status": "expired",
        "subscription_end_date": None,
        "is_admin": False,
        "email_verified": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Delete if exists
    await db.users.delete_one({"email": "testuser@test.com"})
    
    # Insert test user
    await db.users.insert_one(test_user)
    print(f"✅ Test user created: {test_user_id}")
    print(f"   Email: testuser@test.com")
    print(f"   Subscription: expired")
    print(f"   End Date: None")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_renewal())
