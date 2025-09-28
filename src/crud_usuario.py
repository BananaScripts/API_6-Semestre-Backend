from db import get_connection
from BaseModel.Usuario import Usuario, UpdateUsuario, CreateUsuario
from auth.auth import hash_senha


#função de criar o usuário     
def create_usuario(usuario:CreateUsuario):
    senha_hash = hash_senha(usuario.senha) #hashear a senha
    with get_connection() as connection: #em todos pega a conexão do banco
        with connection.cursor() as cursor: #e em seguida executa um sql
            cursor.execute(
                "INSERT INTO domrock.usuario (nome, email, senha) VALUES (%s, %s, %s) RETURNING id, nome, email, senha",
                (usuario.nome, usuario.email, senha_hash)
            )
            new_user = cursor.fetchone()
            connection.commit()
            return Usuario(id=new_user[0], nome=new_user[1], email=new_user[2])

#função para pegar as informações do usuário pelo id
def read_usuario_byid(id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, nome, email, senha FROM domrock.usuario WHERE id = %s",(id,)
            )
            user = cursor.fetchone()
            if user:
                return Usuario(id=user[0], nome=user[1], email=user[2])
            return None

#função para pegar as informações do usuário pelo email        
def read_usuario_byemail(email:str):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, nome, email, senha FROM domrock.usuario WHERE email = %s", (email,)
            )
            user = cursor.fetchone()
            if user:
                return Usuario(id=user[0], nome=user[1], email=user[2], senha=user[3])
            return None

#função para atualizar o usuário
def update_usuario(id: int, usuario: UpdateUsuario):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            #pega os dados atuais do usuario
            cursor.execute("SELECT nome, email, senha FROM domrock.usuario WHERE id = %s", (id,))
            current_user = cursor.fetchone()
            if not current_user:
                return None
            
            #cria um usuario atualizado
            updated_user = {
                "nome": usuario.nome if usuario.nome is not None else current_user[0],
                "email": usuario.email if usuario.email is not None else current_user[1],
                "senha": usuario.senha if usuario.senha is not None else current_user[2],
            }

            #atualiza o usuario
            cursor.execute(
                "UPDATE domrock.usuario SET nome = %s, email = %s, senha = %s WHERE id = %s RETURNING id, nome, email, senha",
                (updated_user["nome"], updated_user["email"], updated_user["senha"], id),
            )
            updated_user_data = cursor.fetchone()
            connection.commit()
            return Usuario(id=updated_user_data[0], nome=updated_user_data[1], email=updated_user_data[2])

#função para deletar o usuário        
def delete_usuario(id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM domrock.usuario WHERE id = %s", (id,))
            connection.commit()
