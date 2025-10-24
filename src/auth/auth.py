from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import timezone, datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

#gerar o hash da senha
def hash_senha(senha: str):
    return pwd_context.hash(senha)

#verificar senha
def verifciar_senha(senha_plain: str, senha_hash: str):
    return pwd_context.verify(senha_plain, senha_hash)

#criar token
def criar_token(data: dict, expires: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires or timedelta(minutes=int(os.getenv("TOKEN_TIME_MINUTES"))))
    to_encode.update({"expire": int(expire.timestamp())})
    return jwt.encode(to_encode, os.getenv("CHAVE"), os.getenv("ALGORITMO"))

#verificar token
def verificar_token(token: str):
    try:
        payload = jwt.decode(token, os.getenv("CHAVE"), os.getenv("ALGORITMO"))
        return payload.get("sub")
    except JWTError:
        return None
