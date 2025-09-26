from fastapi import FastAPI, UploadFile, File, HTTPException
from importar import importar_csv
from gerar_relatorios import gerar_relatorios
from enviar_email import enviar_email
from BaseModel.Email import Email
from BaseModel.Upload import Upload
import os
import aiofiles

app = FastAPI(title="Dom Rock Backend")

#criar pasta uploads para salvar localmente por enquanto os csvs
UPLOAD_DIR = "../csv/uploads/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

#recebe upload dos csv, salva localmente e roda o pipeline de importação
@app.post("/upload/{tipo}")
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
@app.post("/relatorios/enviar")
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

#só pra ver se o servidor está rodando
@app.get("/")
def check():
    return {"status": "ok", "msg": "API funfando"}
