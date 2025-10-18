from fastapi import FastAPI, UploadFile, File, HTTPException, status, Query, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from importar import importar_csv
from gerar_relatorios import gerar_relatorios
from enviar_email import enviar_email
import crud_usuario
import crud_dados
from auth.auth import verifciar_senha, criar_token
from BaseModel.Email import Email
from BaseModel.Upload import Upload
from BaseModel.Usuario import Usuario, UpdateUsuario, CreateUsuario
from BaseModel.Dados import Venda, Estoque
import os
import aiofiles
from fastapi import FastAPI
from gerar_relatorios import gerar_metricas_domrock


app = FastAPI(title="Dom Rock Backend")

#criar pasta uploads para salvar localmente por enquanto os csvs
UPLOAD_DIR = "../csv/uploads/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

#recebe upload dos csv, salva localmente e roda o pipeline de importação
@app.post("/upload/{tipo}", status_code=status.HTTP_201_CREATED)
async def upload_csv(tipo: Upload, file: UploadFile = File(...)):

    if tipo not in Upload:
        raise HTTPException(status_code=400, detail="Tipo inválido. Use 'vendas' ou 'estoque'")

    filepath = os.path.join(UPLOAD_DIR, file.filename)

    try:
        async with aiofiles.open(filepath, "wb") as out_file:
            while content := await file.read(1024):
                await out_file.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {str(e)}")

    try:
        importar_csv(filepath, tipo)
        return {"status": "sucesso", "arquivo": file.filename, "tipo": tipo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#enviar os relatório em formato csv por email
@app.post("/relatorios/enviar", status_code=status.HTTP_200_OK)
def gerar_e_enviar(email:Email, assunto: str, corpo: str):
    try:
        arquivos = gerar_relatorios()

        enviar_email(
            destinatario= email.email,
            arquivos = arquivos,
            assunto = assunto,
            corpo = corpo
        )

        return{"status": "sucesso", "msg": f"Relatórios enviados para {email}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#criar usuario   
@app.post("/usuario", response_model=Usuario, status_code=status.HTTP_201_CREATED)
def create_usuario(usuario: CreateUsuario):
    db_user = crud_usuario.read_usuario_byemail(email = usuario.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    return crud_usuario.create_usuario(usuario)

#pegar usuario
@app.get("/usuario/{usuario_id}", response_model=Usuario, status_code=status.HTTP_200_OK)
def read_usuario(usuario_id: int):
    db_user = crud_usuario.read_usuario_byid(id=usuario_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return db_user

#atualizar usuario
@app.put("/usuario/{usuario_id}", response_model=Usuario, status_code=status.HTTP_200_OK)
def update_usuario(usuario_id:int, usuario:UpdateUsuario):
    updated_user = crud_usuario.update_usuario(id=usuario_id, usuario=usuario)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return updated_user

#deletar usuario
@app.delete("/usuario/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_usuario(usuario_id:int):
    delete_user = usuario_id
    if delete_user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return crud_usuario.delete_usuario(id=usuario_id)

#retornar os dados de vendas
@app.get("/vendas", response_model=List[Venda])
def listar_vendas(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)):
    try:
        return crud_dados.get_vendas(skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#retornar os dados do estoque
@app.get("/estoque", response_model=List[Estoque])
def listar_estoque(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)):
    try:
        return crud_dados.get_estoque(skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#logar o usuário por email    
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = crud_usuario.read_usuario_byemail(form_data.username) #busca o usuário

    #se não achar ou senha estiver errada retorna erro 401
    if not user or not verifciar_senha(form_data.password, user.senha) :
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    #cria e e retorna o token   
    token = criar_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/metricas")
def metricas_domrock():
    return gerar_metricas_domrock()

#só pra ver se o servidor está rodando
@app.get("/")
def check():
    return {"status": "ok", "msg": "API funfando"}
