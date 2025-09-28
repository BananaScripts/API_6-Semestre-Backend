import os
import pandas as pd
from dotenv import load_dotenv
import re
from typing import Dict
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
SENHA_APP = os.getenv("SENHA_APP")


def enviar_email(destinatario: str, arquivos: Dict[str, bytes] , assunto: str, corpo: str):
    
    msg = MIMEMultipart()
    msg["From"] = EMAIL_REMETENTE
    msg["To"] = destinatario
    msg["Subject"] = assunto
    msg.attach(MIMEText(corpo, "plain"))

    for nome_arquivo, csv_bytes in arquivos.items():
        part = MIMEBase("application", "octet-stream")
        part.set_payload(csv_bytes)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={nome_arquivo}.csv")
        msg.attach(part)

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL_REMETENTE, SENHA_APP)
    server.sendmail(EMAIL_REMETENTE, destinatario, msg.as_string())
    server.quit()

    print(f"E-mail enviado para {destinatario}")
