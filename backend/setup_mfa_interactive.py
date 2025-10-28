#!/usr/bin/env python3
"""
Script interativo para configurar MFA para administrador
"""
import requests
import json
import sys
from getpass import getpass

API_URL = "http://localhost:8001/api"

def setup_mfa():
    print("═══════════════════════════════════════════════════════════════")
    print("         AudioMedic - Configuração de MFA (Admin)")
    print("═══════════════════════════════════════════════════════════════\n")
    
    # Step 1: Login
    print("📝 Passo 1: Login do Administrador\n")
    email = input("Email do admin: ").strip()
    password = getpass("Senha: ")
    
    print("\n🔐 Fazendo login...")
    try:
        login_response = requests.post(
            f"{API_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=10
        )
        
        if login_response.status_code != 200:
            print(f"❌ Erro no login: {login_response.json().get('detail', 'Erro desconhecido')}")
            return False
        
        token = login_response.json()['access_token']
        print("✅ Login realizado com sucesso!\n")
        
    except Exception as e:
        print(f"❌ Erro ao conectar: {str(e)}")
        return False
    
    # Step 2: Setup MFA
    print("═══════════════════════════════════════════════════════════════")
    print("📱 Passo 2: Configurar MFA\n")
    print("Gerando QR Code e códigos de backup...\n")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        setup_response = requests.post(
            f"{API_URL}/auth/setup-mfa",
            headers=headers,
            timeout=10
        )
        
        if setup_response.status_code != 200:
            print(f"❌ Erro ao configurar MFA: {setup_response.json().get('detail', 'Erro desconhecido')}")
            return False
        
        mfa_data = setup_response.json()
        
        print("✅ MFA configurado com sucesso!\n")
        print("═══════════════════════════════════════════════════════════════")
        print("📱 QR CODE PARA AUTENTICADOR")
        print("═══════════════════════════════════════════════════════════════\n")
        
        # Display QR code (base64 image)
        qr_code = mfa_data['qr_code']
        print("QR Code Base64 (cole no navegador como data URI):")
        print(f"data:image/png;base64,{qr_code[:100]}...\n")
        
        print("Ou use o código secreto manualmente:")
        print(f"🔑 Secret: {mfa_data['secret']}\n")
        
        print("═══════════════════════════════════════════════════════════════")
        print("💾 CÓDIGOS DE BACKUP (GUARDE EM LOCAL SEGURO!)")
        print("═══════════════════════════════════════════════════════════════\n")
        
        for i, code in enumerate(mfa_data['backup_codes'], 1):
            print(f"  {i:2d}. {code}")
        
        print("\n═══════════════════════════════════════════════════════════════")
        print("⚠️  IMPORTANTE:")
        print("   1. Abra seu aplicativo autenticador (Google Authenticator, Authy, etc)")
        print("   2. Escaneie o QR code acima OU digite o código secreto manualmente")
        print("   3. O app mostrará um código de 6 dígitos que muda a cada 30 segundos")
        print("═══════════════════════════════════════════════════════════════\n")
        
        # Save QR code to file
        with open('/tmp/audiomedic_qr.txt', 'w') as f:
            f.write(f"data:image/png;base64,{qr_code}\n\n")
            f.write(f"Secret: {mfa_data['secret']}\n\n")
            f.write("Backup Codes:\n")
            for code in mfa_data['backup_codes']:
                f.write(f"  {code}\n")
        
        print("💾 QR Code e códigos salvos em: /tmp/audiomedic_qr.txt\n")
        
    except Exception as e:
        print(f"❌ Erro ao configurar MFA: {str(e)}")
        return False
    
    # Step 3: Verify MFA
    print("═══════════════════════════════════════════════════════════════")
    print("✅ Passo 3: Confirmar MFA\n")
    
    print("Digite o código de 6 dígitos do seu aplicativo autenticador:")
    code = input("Código: ").strip()
    
    print("\n🔐 Verificando código...")
    
    try:
        verify_response = requests.post(
            f"{API_URL}/auth/confirm-mfa",
            headers=headers,
            json={"code": code},
            timeout=10
        )
        
        if verify_response.status_code != 200:
            print(f"❌ Código inválido: {verify_response.json().get('detail', 'Erro desconhecido')}")
            print("\n⚠️  O MFA foi configurado, mas não confirmado.")
            print("   Você pode tentar novamente executando este script.")
            return False
        
        print("\n✅ MFA ATIVADO COM SUCESSO!\n")
        print("═══════════════════════════════════════════════════════════════")
        print("🎉 Parabéns! MFA está agora ativo para sua conta.")
        print("═══════════════════════════════════════════════════════════════\n")
        print("Agora você pode:")
        print("  ✅ Renovar assinaturas de usuários")
        print("  ✅ Alterar status de admin de usuários")
        print("  ✅ Todas as operações administrativas\n")
        
        print("⚠️  LEMBRETE:")
        print("  - Guarde os códigos de backup em local seguro")
        print("  - Se perder acesso ao autenticador, use os códigos de backup")
        print("  - Os códigos estão salvos em: /tmp/audiomedic_qr.txt\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar código: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        success = setup_mfa()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}")
        sys.exit(1)
