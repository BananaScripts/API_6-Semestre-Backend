from pydantic import BaseModel
from typing import Optional
from pydantic import EmailStr

class Usuario(BaseModel):
    nome:str
    email:EmailStr
    senha:str

class CreateUsuario(Usuario):
    pass

class UpdateUsuario(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    senha: Optional[str] = None