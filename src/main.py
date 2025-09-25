from fastapi import FastAPI, UploadFile, File, HTTPException
from importar import importar_csv
import os
import aiofiles

app = FastAPI(title="Dom Rock Backend")

#criar pastas uploads e relatorios para salvar localmente por enquanto os csvs
UPLOAD_DIR = "../csv/uploads/"
os.makedirs(UPLOAD_DIR, exist_ok=True)
RELATORIO_DIR = "../csv/relatorios/"
os.makedirs(RELATORIO_DIR, exist_ok=True)

#recebe upload dos csv, salva localmente e roda o pipeline de importação
@app.post("/upload/{tipo}")
async def upload_csv(tipo: str, file: UploadFile = File(...)):

    if tipo not in ["vendas", "estoque"]:
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

#só pra ver se o servidor está rodando
@app.get("/")
def check():
    return {"status": "ok", "msg": "API funfando"}
