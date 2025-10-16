#!/usr/bin/env python3
"""
Script para criar usuário administrador no AudioMedic
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pymongo import MongoClient
import bcrypt
import uuid
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from getpass import getpass

# Load environment variables
load_dotenv()

def create_admin():
    """Create admin user"""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║         AudioMedic - Criar Usuário Administrador           ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    # Get admin details
    print("📝 Informações do Administrador:")
    print()
    
    name = input("Nome completo: ").strip()
    if not name:
        print("❌ Nome não pode estar vazio")
        return False
    
    email = input("Email: ").strip().lower()
    if not email or '@' not in email:
        print("❌ Email inválido")
        return False
    
    # Password validation
    while True:
        password = getpass("Senha (mínimo 8 caracteres, maiúscula, minúscula, número, especial): ")
        confirm = getpass("Confirme a senha: ")
        
        if password != confirm:
            print("❌ Senhas não conferem. Tente novamente.")
            continue
        
        # Validate password strength
        if len(password) < 8:
            print("❌ Senha muito curta (mínimo 8 caracteres)")
            continue
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*(),.?":{}|<>_-+=[]\\;\\'`~' for c in password)
        
        if not all([has_upper, has_lower, has_digit, has_special]):
            print("❌ Senha deve conter:")
            print("   - Pelo menos uma letra maiúscula")
            print("   - Pelo menos uma letra minúscula")
            print("   - Pelo menos um número")
            print("   - Pelo menos um caractere especial")
            continue
        
        break
    
    print()
    print("🔌 Conectando ao MongoDB...")
    
    try:
        # Connect to MongoDB
        mongo_url = os.environ.get('MONGO_URL')
        if not mongo_url:
            print("❌ MONGO_URL não configurado no .env")
            return False
        
        client = MongoClient(mongo_url)
        db_name = os.environ.get('DB_NAME', 'audiomedic_db')
        db = client[db_name]
        
        # Check if user already exists
        existing = db.users.find_one({"email": email})
        if existing:
            print(f"❌ Usuário com email {email} já existe")
            overwrite = input("Deseja sobrescrever? (s/n): ").strip().lower()
            if overwrite != 's':
                print("Operação cancelada")
                return False
            
            # Delete existing user
            db.users.delete_one({"email": email})
            print("✅ Usuário anterior removido")
        
        # Hash password
        print("🔐 Criptografando senha...")
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
        
        # Create admin document
        admin_id = str(uuid.uuid4())
        subscription_end = datetime.now(timezone.utc) + timedelta(days=365)
        
        admin_doc = {
            "id": admin_id,
            "email": email,
            "name": name,
            "hashed_password": hashed_pw,
            "subscription_status": "active",
            "subscription_end_date": subscription_end.isoformat(),
            "is_admin": True,
            "email_verified": True,
            "mfa_enabled": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Insert into database
        print("💾 Salvando no banco de dados...")
        db.users.insert_one(admin_doc)
        
        print()
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║              ✅ Administrador Criado!                       ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print()
        print(f"📧 Email: {email}")
        print(f"👤 Nome: {name}")
        print(f"🔑 ID: {admin_id}")
        print(f"📅 Assinatura válida até: {subscription_end.strftime('%d/%m/%Y')}")
        print()
        print("⚠️  IMPORTANTE:")
        print("   - Guarde suas credenciais em local seguro")
        print("   - Use MFA para maior segurança (configurar no painel admin)")
        print("   - Altere a senha periodicamente")
        print()
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        success = create_admin()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}")
        sys.exit(1)
