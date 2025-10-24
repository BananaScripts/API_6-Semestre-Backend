import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from Classes import Intencao as intencoes
import pandas as pd
from crud_dados import (
    get_total_produtos_distintos,
    get_total_itens_estoque,
    get_peso_total_faturado,
    get_top_n_produtos_estoque,
    get_top_n_cidades_faturamento
)


#associa cada intenção a função que deve ser executada
intencao_to_function = {
    intencoes.Intencao.TOTAL_ITENS_ESTOQUE: get_total_itens_estoque,
    intencoes.Intencao.PESO_TOTAL_FATURADO: get_peso_total_faturado,
    intencoes.Intencao.TOP_PRODUTOS_ESTOQUE: get_top_n_produtos_estoque,
    intencoes.Intencao.TOP_CIDADES_FATURAMENTO: get_top_n_cidades_faturamento,
    intencoes.Intencao.TOTAL_PRODUTOS_DISTINTOS: get_total_produtos_distintos
}

#carrega as oerguntas do csv e as associa a uma intenção
def carregar_pergutas(path="../csv/perguntas.csv"):
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        print(f"Arquivo não encontrado em {path}")
        #fallback para um conjunto mínimo se o CSV não fro encontrado
        return{
            "Qual o total de itens em estoque?": intencoes.Intencao.TOTAL_ITENS_ESTOQUE,
            "Quais os principais produtos?": intencoes.Intencao.TOP_PRODUTOS_ESTOQUE,
            "Quais as cidades com maior faturamento?": intencoes.Intencao.TOP_CIDADES_FATURAMENTO
        }

    #dicionário para mapear palavras-chave a intenções
    keyword_intencao = {
        ("total", "itens", "estoque", "depósito", "armazenamento"): intencoes.Intencao.TOTAL_ITENS_ESTOQUE,
        ("quantos", "produtos", "diferentes", "distintos", "cadastrados"): intencoes.Intencao.TOTAL_PRODUTOS_DISTINTOS,
        ("peso", "vendido", "faturamento", "volume de vendas", "receita"): intencoes.Intencao.PESO_TOTAL_FATURADO,
        ("principais", "produtos", "mais vendidos", "contribuíram"): intencoes.Intencao.TOP_PRODUTOS_ESTOQUE,
        ("cidades", "regiões", "compram conosco"): intencoes.Intencao.TOP_CIDADES_FATURAMENTO,
    }

    training_data = {}
    for pergunta in df['pergunta']:
        pergunta_lower = pergunta.lower()
        match_intencao = intencoes.Intencao.DESCONHECIDO
        for keywords, intencao in keyword_intencao.items():
            if any(keyword in pergunta_lower for keyword in keywords):
                match_intencao = intencao
                break
        #apenas adiciona se uma intenção relevante for encontrada
        if match_intencao != intencoes.Intencao.DESCONHECIDO:
            training_data[pergunta] = match_intencao
    return training_data 

class Chatbot:
    def __init__(self, training_data):
        if not training_data:
            raise ValueError("Os dados de treinamento não podem estar vazios")

        self.perguntas_treinamento = list(training_data.keys())
        self.intencoes_treinamento = list(training_data.values())
        
        self.vectorizer = TfidfVectorizer()
        self.pergunta_vetores = self.vectorizer.fit_transform(self.perguntas_treinamento)

    def _extrair_numero(self, texto, default=5):
        numeros = re.findall(r'\d+', texto)
        return int(numeros[0]) if numeros else default

    def prever_intencao(self, pergunta_usuario):
        if not pergunta_usuario.strip():
            return intencoes.Intencao.DESCONHECIDO
        
        pergunta_usuario_vetor = self.vectorizer.transform([pergunta_usuario])
        similaridades = cosine_similarity(pergunta_usuario_vetor, self.pergunta_vetores)
        best_match_index = similaridades.argmax()
        
        #mimiar de confiança
        if similaridades[0, best_match_index] < 0.25:
            return intencoes.Intencao.DESCONHECIDO
            
        return self.intencoes_treinamento[best_match_index]

    def get_response(self, intencao, user_question):
        if intencao == intencoes.Intencao.DESCONHECIDO or intencao not in intencao_to_function:
            return "Desculpe, não entendi sua pergunta. Poderia tentar reformular?", "N/A"

        function_to_execute = intencao_to_function[intencao]
        
        try:
            #se a função for parametrizável (aceita 'n')
            if 'top_n' in function_to_execute.__name__:
                n = self._extract_number(user_question, default=5)
                response = function_to_execute(n=n)
            else:
                response = function_to_execute()
            
            #retorna a resposta e a intenção identificada (para depuração/logging)
            return response, intencao
        except Exception as e:
            print(f"Erro ao executar a função para a intenção {intencao}: {e}")
            return "Ocorreu um erro ao buscar sua resposta.", intencao

# 5. INICIALIZAÇÃO DO SISTEMA
# Cria a instância única do chatbot que será usada pela API
training_data = carregar_pergutas()
chatbot = Chatbot(training_data)


