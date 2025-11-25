
from .Intencao import Intencao
from .logger import log_info, log_error
from .nlp_utils import NlpEngine
from crud_dados import execute_query_from_components # Importaremos a nova função

class Chatbot:
    """Orquestra a interação entre a NLP Engine e a execução da consulta."""
    def __init__(self, nlp_engine: NlpEngine):
        self.nlp_engine = nlp_engine
        log_info("Chatbot inicializado com a nova NlpEngine Híbrida.")

    def get_response(self, user_question: str) -> tuple[dict, str]:
        """
        Processa a pergunta do usuário e retorna a resposta e a intenção identificada.
        """
        if not user_question:
            return {"erro": "A pergunta não pode ser vazia."}, "DESCONHECIDO"

        # 1. Extrair componentes da consulta usando a NlpEngine Híbrida
        components = self.nlp_engine.predict_components(user_question)
        intent_name = components["intent"].name

        # 2. Lidar com intenções de sistema (DESCONHECIDO, FORA_DE_ESCOPO)
        if components["intent"] == Intencao.DESCONHECIDO:
            log_info("Intenção não identificada pela NlpEngine.")
            return {"erro": "Desculpe, não entendi sua pergunta."}, intent_name
        
        if components["intent"] == Intencao.FORA_DE_ESCOPO:
            log_info("Pergunta classificada como FORA_DE_ESCOPO.")
            return {"resposta": ["Não tenho informações sobre pedidos não faturados, cancelados ou devolvidos."]}, intent_name

        # 3. Chamar a nova função de construção de query dinâmica
        try:
            # A função execute_query_from_components agora retorna uma lista.
            result_list = execute_query_from_components(components)
            
            # CORREÇÃO: A variável agora é uma lista (result_list), 
            # então o .splitlines() foi removido pois não é necessário (e causa o erro).
            formatted_response = {"resposta": result_list}
            
            log_info(f"Consulta para a intenção {intent_name} foi bem-sucedida.")
            return formatted_response, intent_name

        except Exception as e:
            log_error(f"Erro ao executar a consulta para componentes {components}: {e}")
            return {"erro": "Ocorreu um erro interno ao buscar os dados."}, intent_name

# =====================
# 🚀 INICIALIZAÇÃO SINGLETON
# =====================

nlp_engine_instance = NlpEngine(csv_path="../csv/perguntas.csv")
chatbot_instance = Chatbot(nlp_engine=nlp_engine_instance)
