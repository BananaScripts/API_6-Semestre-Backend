# Como rodar o backend

## Requisitos

- **Python 3.10+**  
- **PostgreSQL** instalado localmente (pode ser o [PostgreSQL oficial](https://www.postgresql.org/download/))
- **pip** (gerenciador de pacotes Python)

## Instalação das dependências

No terminal, na raiz do projeto, execute:

```sh
pip install -r requirements.txt
```

## Configuração do banco de dados local (usando pgAdmin)

1. **Abra o pgAdmin**

2. **Conecte-se ao servidor** usando seu usuário e senha

3. **Crie o banco de dados:**
   - Clique com o botão direito em "Databases" (Bancos de Dados) no painel à esquerda.
   - Selecione "Create" > "Database...".
   - Dê o nome `domrock` e clique em "Save". </br>
   <img width="600px" alt="image" src="https://github.com/user-attachments/assets/abe80b5f-7f13-4382-8b40-9b65d0bb91e8" />
   <img width="600px" alt="image-1" src="https://github.com/user-attachments/assets/37736d73-8a11-4a26-a8c2-8dc8937fa1a8" />


4. **Crie as tabelas e estrutura:**
   - Com o banco `domrock` selecionado, clique em "Query Tool" (Ferramenta de Consulta).
   - Abra o arquivo `sql/domrock.sql` no seu editor de texto, copie todo o conteúdo.
   - Cole o conteúdo no Query Tool do pgAdmin.
   - Clique em "Executar" para rodar o script e criar as tabelas. </br>
   <img width="600px" alt="image-2" src="https://github.com/user-attachments/assets/520104a8-3288-4d07-8eed-01e4092128fa" />
   <img width="600px" alt="image-3" src="https://github.com/user-attachments/assets/7e1b5588-678e-438c-b396-a13cbd87f543" />
   <img width="600px" alt="image-4" src="https://github.com/user-attachments/assets/d61d17b4-2a2d-4742-b049-df15783ce615" />

> **Obs:**  
> O usuário padrão é `postgres`.  
> Altere seu .env se necessário para combinar com sua configuração local.

## Rodando o backend

1. Entre na pasta `src`:

   ```sh
   cd src
   ```

2. Inicie o servidor FastAPI com Uvicorn:

   ```sh
   uvicorn main:app --reload
   ```

3. Acesse a API em [http://127.0.0.1:8000](http://127.0.0.1:8000))  
   A documentação interativa estará disponível em [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)


