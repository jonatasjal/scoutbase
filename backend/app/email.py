# app/email.py - envio de e-mails (Fase 15)
# Enquanto SMTP_HOST não estiver preenchido no .env, aqui é SIMULACAO:
# o token só aparece no console do servidor (e na resposta, se DEBUG=true)
import smtplib                      # biblioteca padrão do Python p/ enviar e-mail
from email.mime.text import MIMEText  # monta a mensagem do e-mail

from app.config import settings     # lê SMTP_* e DEBUG do .env

def enviar_email_reset(email: str, token: str) -> bool:
    '''
    Manda o link de redefinição. True = enviou de verdade; False = simulou
    '''
    # O link que o usuário vai clicar: passa o token na URL (é como se fosse o 'recibo')
    link = f'https://scoutbase-two.vercel.app/esqueci-senha?token={token}'

    if not settings.smtp_host:
        # SEM SMTP: modo simulação - imprime no terminal do servidor
        print(f'[SIMULAÇÃO - sem SMTP] Token para {email}: {link}')
        return False

    # ---- SMTP configurado: enio real (funciona quando preencher o .env)
    msg = MIMEText(f'Oi! Para redefinir sua senha, acesse: \n{link}\n\nSe não foi você, ignore este e-mail')
    msg['Subject'] = 'ScoutBase - redefinição de senha'
    msg['From'] = settings.smtp_from
    msg['To'] = email
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as servidor:
        servidor.starttls()         # criptografa a conversa (TLS)
        servidor.login(settings.smtp_user, settings.smtp_password)
        servidor.sendmail(settings.smtp_from, [email], msg.as_string())
    return True
