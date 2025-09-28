from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from crud_usuario import read_usuario_byemail
from auth import verificar_token

#esquema de autenticação
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

#extrai o email do token, valida o usuário e retorna os dados do usuario autenticado
def get_usuario_logado(token: str = Depends(oauth2_scheme)):
    email = verificar_token(token)
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou não autorizado")
    
    usuario = read_usuario_byemail(email)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado ou não autorizado")
    
    return usuario