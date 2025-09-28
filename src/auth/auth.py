from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import timezone, datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

#contexto pro hash da senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated = "auto")

#gerar o hash da senha
def hash_senha(senha: str):
    senha_bytes = senha.encode("utf-8")[:72] #trunca para 72 bytes
    senha_truncada = senha_bytes.decode('utf-8', 'ignore')  #remove caracteres quebrados
    return pwd_context.hash(senha_truncada)


#verifica se a senha informada é igual a senha armazenada com hash
def verifciar_senha(senha_plain: str, senha_hash: str):
    senha_bytes = senha_plain.encode("utf-8")[:72]
    return pwd_context.verify(senha_bytes, senha_hash)

#criar o token
def criar_token(data: dict, expires: timedelta = None):
    to_encode = data.copy() #copia os dados recebidos
    expire = datetime.now(timezone.utc) + (expires or  timedelta(minutes=int(os.getenv("TOKEN_TIME_MINUTES")))) #define a data de expiração do token usando o expire fornecido ou o do .env
    to_encode.update({"expire": int(expire.timestamp())}) #adiciona o expire no dicionário dos dados
    return jwt.encode(to_encode, os.getenv("CHAVE"), os.getenv("ALGORITMO")) #codifica o jwt

#verifica se o token é válido
def verificar_token(token: str):
    try:
        #decodifica o token e retorna o valor "sub" como identificaro do usuário
        payload = jwt.decode(token, os.getenv("CHAVE"), os.getenv("ALGORITMO"))
        return payload.get("sub")
    except JWTError:
        return None
