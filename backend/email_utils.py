"""Email utilities for sending verification and password reset emails"""
import os
import logging
from typing import Optional
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

# SMTP Configuration from environment
SMTP_HOST = os.environ.get('SMTP_HOST', '')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_FROM_EMAIL = os.environ.get('SMTP_FROM_EMAIL', 'noreply@audiomedic.com')
SMTP_FROM_NAME = os.environ.get('SMTP_FROM_NAME', 'AudioMedic')
SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true'
SMTP_ENABLED = bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)

# Frontend URL for links
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://medtranscribe-9.preview.emergentagent.com')


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """
    Send email via SMTP or simulate if not configured.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML body
        text_content: Plain text body (optional)
    
    Returns:
        True if sent successfully, False otherwise
    """
    if not SMTP_ENABLED:
        # Simulate email sending (log to console)
        logger.warning("📧 SMTP not configured - Simulating email send")
        logger.info(f"""
╔══════════════════════════════════════════════════════════════╗
║                    📧 EMAIL SIMULADO                         ║
╠══════════════════════════════════════════════════════════════╣
║ Para: {to_email:<54} ║
║ Assunto: {subject:<51} ║
╠══════════════════════════════════════════════════════════════╣
║ CONTEÚDO:                                                    ║
║                                                              ║
{html_content[:500]}
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        return True
    
    try:
        # Create message
        message = MIMEMultipart('alternative')
        message['From'] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        message['To'] = to_email
        message['Subject'] = subject
        
        # Add text and HTML parts
        if text_content:
            part1 = MIMEText(text_content, 'plain')
            message.attach(part1)
        
        part2 = MIMEText(html_content, 'html')
        message.attach(part2)
        
        # Send email
        if SMTP_USE_TLS:
            await aiosmtplib.send(
                message,
                hostname=SMTP_HOST,
                port=SMTP_PORT,
                username=SMTP_USER,
                password=SMTP_PASSWORD,
                start_tls=True
            )
        else:
            await aiosmtplib.send(
                message,
                hostname=SMTP_HOST,
                port=SMTP_PORT,
                username=SMTP_USER,
                password=SMTP_PASSWORD,
                use_tls=True
            )
        
        logger.info(f"✅ Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
        return False


async def send_verification_email(email: str, token: str, name: str) -> bool:
    """
    Send email verification link.
    
    Args:
        email: User email
        token: Verification token
        name: User name
    
    Returns:
        True if sent successfully
    """
    verification_link = f"{FRONTEND_URL}/verify-email?token={token}"
    
    subject = "Verificação de Email - AudioMedic"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #0f172a; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #0284c7 0%, #0ea5e9 100%); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
            .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 12px 12px; }}
            .button {{ display: inline-block; background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%); color: white; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; }}
            .footer {{ text-align: center; color: #64748b; font-size: 14px; margin-top: 30px; }}
            .token {{ background: #e0f2fe; padding: 12px; border-left: 4px solid #0ea5e9; margin: 20px 0; font-family: monospace; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔒 AudioMedic</h1>
                <p>Verificação de Email</p>
            </div>
            <div class="content">
                <h2>Olá, {name}!</h2>
                <p>Obrigado por se registrar no AudioMedic. Para ativar sua conta, por favor verifique seu endereço de email clicando no botão abaixo:</p>
                
                <div style="text-align: center;">
                    <a href="{verification_link}" class="button">Verificar Email</a>
                </div>
                
                <p>Ou copie e cole o link abaixo no seu navegador:</p>
                <div class="token">{verification_link}</div>
                
                <p><strong>Este link expira em 24 horas.</strong></p>
                
                <p>Se você não criou uma conta no AudioMedic, por favor ignore este email.</p>
                
                <div class="footer">
                    <p>© 2025 AudioMedic - Sistema de Transcrição Médica</p>
                    <p>Este é um email automático, por favor não responda.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Olá, {name}!
    
    Obrigado por se registrar no AudioMedic.
    
    Para ativar sua conta, por favor verifique seu endereço de email acessando o link abaixo:
    
    {verification_link}
    
    Este link expira em 24 horas.
    
    Se você não criou uma conta no AudioMedic, por favor ignore este email.
    
    © 2025 AudioMedic
    """
    
    return await send_email(email, subject, html_content, text_content)


async def send_password_reset_email(email: str, token: str, name: str) -> bool:
    """
    Send password reset link.
    
    Args:
        email: User email
        token: Reset token
        name: User name
    
    Returns:
        True if sent successfully
    """
    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"
    
    subject = "Recuperação de Senha - AudioMedic"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #0f172a; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #0284c7 0%, #0ea5e9 100%); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
            .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 12px 12px; }}
            .button {{ display: inline-block; background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%); color: white; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; }}
            .warning {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px; margin: 20px 0; }}
            .footer {{ text-align: center; color: #64748b; font-size: 14px; margin-top: 30px; }}
            .token {{ background: #e0f2fe; padding: 12px; border-left: 4px solid #0ea5e9; margin: 20px 0; font-family: monospace; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 AudioMedic</h1>
                <p>Recuperação de Senha</p>
            </div>
            <div class="content">
                <h2>Olá, {name}!</h2>
                <p>Recebemos uma solicitação para redefinir a senha da sua conta AudioMedic.</p>
                
                <p>Para criar uma nova senha, clique no botão abaixo:</p>
                
                <div style="text-align: center;">
                    <a href="{reset_link}" class="button">Redefinir Senha</a>
                </div>
                
                <p>Ou copie e cole o link abaixo no seu navegador:</p>
                <div class="token">{reset_link}</div>
                
                <div class="warning">
                    <strong>⚠️ Importante:</strong>
                    <ul style="margin: 10px 0;">
                        <li>Este link expira em 1 hora</li>
                        <li>Pode ser usado apenas uma vez</li>
                        <li>Se você não solicitou esta alteração, ignore este email</li>
                    </ul>
                </div>
                
                <p>Por segurança, recomendamos que você:</p>
                <ul>
                    <li>Use uma senha forte com no mínimo 8 caracteres</li>
                    <li>Inclua letras maiúsculas e minúsculas</li>
                    <li>Adicione números e caracteres especiais</li>
                </ul>
                
                <div class="footer">
                    <p>© 2025 AudioMedic - Sistema de Transcrição Médica</p>
                    <p>Este é um email automático, por favor não responda.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Olá, {name}!
    
    Recebemos uma solicitação para redefinir a senha da sua conta AudioMedic.
    
    Para criar uma nova senha, acesse o link abaixo:
    
    {reset_link}
    
    ⚠️ IMPORTANTE:
    - Este link expira em 1 hora
    - Pode ser usado apenas uma vez
    - Se você não solicitou esta alteração, ignore este email
    
    Por segurança, use uma senha forte com no mínimo 8 caracteres, incluindo letras maiúsculas, minúsculas, números e caracteres especiais.
    
    © 2025 AudioMedic
    """
    
    return await send_email(email, subject, html_content, text_content)


async def send_mfa_setup_email(email: str, name: str) -> bool:
    """
    Send MFA setup notification.
    
    Args:
        email: User email
        name: User name
    
    Returns:
        True if sent successfully
    """
    subject = "Autenticação em Duas Etapas Ativada - AudioMedic"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #0f172a; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
            .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 12px 12px; }}
            .success {{ background: #d1fae5; border-left: 4px solid #10b981; padding: 12px; margin: 20px 0; }}
            .footer {{ text-align: center; color: #64748b; font-size: 14px; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 AudioMedic</h1>
                <p>Segurança Aprimorada</p>
            </div>
            <div class="content">
                <h2>Olá, {name}!</h2>
                
                <div class="success">
                    <strong>✅ Autenticação em Duas Etapas (MFA) Ativada</strong>
                </div>
                
                <p>A autenticação em duas etapas foi ativada com sucesso na sua conta AudioMedic.</p>
                
                <p>A partir de agora, você precisará:</p>
                <ul>
                    <li>Sua senha</li>
                    <li>Um código de 6 dígitos do aplicativo autenticador</li>
                </ul>
                
                <p><strong>Códigos de backup:</strong> Guarde seus códigos de backup em um local seguro. Eles podem ser usados caso você perca acesso ao aplicativo autenticador.</p>
                
                <p>Se você não ativou a autenticação em duas etapas, entre em contato com o suporte imediatamente.</p>
                
                <div class="footer">
                    <p>© 2025 AudioMedic - Sistema de Transcrição Médica</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Olá, {name}!
    
    ✅ Autenticação em Duas Etapas (MFA) Ativada
    
    A autenticação em duas etapas foi ativada com sucesso na sua conta AudioMedic.
    
    A partir de agora, você precisará:
    - Sua senha
    - Um código de 6 dígitos do aplicativo autenticador
    
    Guarde seus códigos de backup em um local seguro.
    
    Se você não ativou a autenticação em duas etapas, entre em contato com o suporte imediatamente.
    
    © 2025 AudioMedic
    """
    
    return await send_email(email, subject, html_content, text_content)
