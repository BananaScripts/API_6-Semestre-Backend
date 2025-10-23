from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import os

path_roteiro = os.path.join("roteiro", "roteiro.json")

with open(path_roteiro, "r", encoding="utf-8") as arquivo:
    roteiro = json.load(arquivo)

class Chatbot:
    
    def __init__(self, perguntas_e_respostas):

        self.perguntas_e_respostas = perguntas_e_respostas
        self.perguntas = list(self.perguntas_e_respostas.keys())

        self.vetorizador = TfidfVectorizer()
        self.vetores_perguntas = self.vetorizador.fit_transform(self.perguntas)
    
    def encontrar_melhor_combinacao(self, pergunta_usuario):
        
        if not pergunta_usuario:
            return None
    
        # Cria o vetor TF-IDF da pergunta do usuário
        pergunta_usuario_vetor = self.vetorizador.transform([pergunta_usuario])

        # Calcula similaridade entre a pergunta do usuário e todas as perguntas
        similaridades = cosine_similarity(pergunta_usuario_vetor, self.vetores_perguntas)

        # Obtém o índice da melhor correspondência
        melhor_similaridade_index = similaridades.argmax()

        # Retorna a pergunta correspondente
        return self.perguntas[melhor_similaridade_index]
    
    def get_response(self, pergunta):
        return self.perguntas_e_respostas.get(pergunta, "Desculpe, não entendi sua pergunta.")
    

# Exemplo de uso
if __name__ == '__main__':
    chatbot = Chatbot(roteiro)
    
    pergunta_usuario = "qual a minha idade"
    
    melhor_pergunta = chatbot.encontrar_melhor_combinacao(pergunta_usuario)
    resposta = chatbot.get_response(melhor_pergunta)
    
    print(f"Pergunta do usuário: {pergunta_usuario}")
    print(f"Pergunta correspondente no roteiro: {melhor_pergunta}")
    print(f"Resposta: {resposta}")
