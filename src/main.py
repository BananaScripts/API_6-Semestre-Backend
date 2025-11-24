from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect, status, Query, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import aiofiles
from dotenv import load_dotenv
from io import BytesIO
import pandas as pd
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
from Classes.Chatbot import chatbot_instance 
import os
import aiofiles

app = FastAPI(title="Dom Rock Backend")

# ✅ Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Pode restringir para ["http://localhost:3000"] ou domínio do seu front
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Criar pasta uploads para salvar CSVs
UPLOAD_DIR = "../csv/uploads/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Carregar variáveis de ambiente
load_dotenv(dotenv_path="src/.env")
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
SENHA_APP = os.getenv("SENHA_APP")

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
        import traceback
        print("ERRO AO IMPORTAR CSV")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def metricas_para_bytes(metricas) -> bytes:
    cleaned = {}
    for chave, valor in metricas.items():
        if isinstance(valor, dict):
            cleaned[chave] = {
                sub_k: (", ".join(sub_v) if isinstance(sub_v, list) else sub_v)
                for sub_k, sub_v in valor.items()
            }
        else:
            cleaned[chave] = valor

    df = pd.DataFrame.from_dict(cleaned, orient="index")
    buffer = BytesIO()
    df.to_csv(buffer, index=True, encoding="utf-8")
    buffer.seek(0)
    return buffer.read()


def metricas_para_texto(metricas: dict) -> str:
    linhas = []
    for chave, valor in metricas.items():
        if isinstance(valor, dict) and 'descricao' in valor:
            linhas.append(valor['descricao'])
        else:
            linhas.append(f"{chave}: {valor}")
    return "\n".join(linhas)

@app.post("/relatorios/enviar", status_code=status.HTTP_200_OK)
def gerar_e_enviar(email: Email, assunto: str, corpo: str = ""):
    try:
        metricas = gerar_relatorios()
        print("DEBUG - Métricas geradas com sucesso:", metricas)

        relatorio_texto = metricas_para_texto(metricas)
        mensagem_final = f"{corpo}\n\n{relatorio_texto}" if corpo else relatorio_texto

        relatorio_bytes = metricas_para_bytes(metricas)

        enviar_email(
            destinatario=email.email,
            assunto=assunto,
            corpo=mensagem_final,
            arquivos={"relatorio_metricas.csv": relatorio_bytes}
        )

        print("DEBUG - E-mail enviado com sucesso!")
        return {"status": "sucesso", "msg": f"Relatórios enviados para {email.email}"}
    except Exception as e:
        import traceback
        print("=== ERRO AO ENVIAR RELATÓRIO ===")
        traceback.print_exc()
        print("===============================")
        raise HTTPException(status_code=500, detail=str(e))
    


#-----------------CRUD Usuário-----------------#

#criar usuario   
@app.post("/usuario", response_model=Usuario, status_code=status.HTTP_201_CREATED)
def create_usuario(usuario: CreateUsuario):
    db_user = crud_usuario.read_usuario_byemail(email=usuario.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email já registrado")
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
def update_usuario(usuario_id: int, usuario: UpdateUsuario):
    updated_user = crud_usuario.update_usuario(id=usuario_id, usuario=usuario)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return updated_user

#deletar usuario
@app.delete("/usuario/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_usuario(usuario_id: int):
    delete_user = usuario_id
    if delete_user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return crud_usuario.delete_usuario(id=usuario_id)



#-----------------Read dos Dados do Banco-----------------#

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
    


#-----------------Login-----------------#

#logar o usuário por email    
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = crud_usuario.read_usuario_byemail(form_data.username)
    if not user or not verifciar_senha(form_data.password, user.senha):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    token = criar_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/")
def check():
    return {"status": "ok", "msg": "API funcionando"}
#-----------------Chatbot-----------------#
@app.websocket("/ws/chatbot")
async def websocket_chatbot_endpoint(websocket: WebSocket):
    await websocket.accept()

    if chatbot_instance is None:
        await websocket.send_json({"erro": "O chatbot não está disponível no momento."})
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return

    try:
        while True:
            user_question = await websocket.receive_text()
            
            # Toda a lógica está encapsulada nesta única chamada
            response_data, matched_intent = chatbot_instance.get_response(user_question)

            await websocket.send_json({
                "original_question": user_question,
                "matched_intent": matched_intent, 
                "answer": response_data
            })

    except WebSocketDisconnect:
        print("Cliente desconectado do chatbot")
    except Exception as e:
        print(f"Erro no websocket do chatbot: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)



