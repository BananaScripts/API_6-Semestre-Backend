import sqlite3
import bcrypt

DB_PATH = "../sql/domrock.db" 

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()
    print(f"Banco criado em: {DB_PATH}")

def seed_user():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    nome = "Admin"
    email = "admin@teste.com"
    senha = "123456"

    hashed_pw = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt())

    try:
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
            (nome, email, hashed_pw.decode("utf-8")),
        )
        conn.commit()
        print("Usuário admin criado!")
    except sqlite3.IntegrityError:
        print("Usuário já existe.")

    conn.close()

if __name__ == "__main__":
    init_db()
    seed_user()
