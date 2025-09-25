import psycopg2
import pandas as pd


import sqlite3
import bcrypt

DB_PATH = "../sql/domrock.db"  

def get_connection():
    return sqlite3.connect(DB_PATH)

def get_user_by_email(email: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, email, senha FROM usuarios WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "nome": row[1], "email": row[2], "senha": row[3]}
    return None

def create_user(nome: str, email: str, senha: str):
    """Cria um usuário novo com senha criptografada"""
    conn = get_connection()
    cursor = conn.cursor()
    hashed_pw = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt())
    try:
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
            (nome, email, hashed_pw.decode("utf-8")),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError("Já existe um usuário com este email")
    finally:
        conn.close()
