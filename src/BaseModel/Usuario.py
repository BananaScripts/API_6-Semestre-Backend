from pydantic import BaseModel
from typing import Optional
from pydantic import EmailStr

class Usuario(BaseModel):
    id: Optional[int] = None
    nome:str
    email:EmailStr
    senha: Optional[str] = None

class CreateUsuario(Usuario):
    pass

class UpdateUsuario(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    senha: Optional[str] = None