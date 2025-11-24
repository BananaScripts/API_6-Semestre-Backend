import re
import numpy as np
import pandas as pd
import unidecode
from sentence_transformers import SentenceTransformer, util
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .Intencao import Intencao
from .logger import log_info, log_error

# ===================================================================
# 🚀 ARQUITETURA CORRIGIDA E ROBUSTA
# ===================================================================

def normalize_text(text: str) -> str:
    if not text: return ""
    text = text.lower()
    text = unidecode.unidecode(text)
    text = re.sub(r'[^a-z0-9\s]', '', text).strip()
    return re.sub(r'\s+', ' ', text)

def extract_number(text: str, default: int = 5) -> int:
    nums = re.findall(r'\d+', text)
    return int(nums[0]) if nums else default

FILTERS_CONFIG = [
    {"regex": r"da cidade de (.*?)(?=\s*e |$)", "db_column": "zs_cidade"},
    {"regex": r"do cliente (.*?)(?=\s*e |$)", "db_column": "cod_cliente"},
    {"regex": r"do produto (.*?)(?=\s*e |$)", "db_column": "produto"}
]

class NlpEngine:
    def __init__(self, csv_path="../csv/perguntas.csv", embed_model_name="all-MiniLM-L6-v2"):
        log_info("Inicializando NlpEngine com Extração de Entidades...")
        self.perguntas_df = self._load_and_process_csv(csv_path)
        self.vectorizer, self.tfidf_vectors = self._build_tfidf_model()
        self.embed_model, self.bert_embeddings = self._build_bert_model(embed_model_name)
        self.rule_based_patterns = {
            "out_of_scope": r"(nao faturado|cancelado|devolvido)",
            "distinct": r"(distintos|diferentes|unicos)",
        }
        log_info("NlpEngine (com Entidades) inicializada.")

    def _load_and_process_csv(self, path):
        try:
            df = pd.read_csv(path)
            df.dropna(subset=['pergunta', 'intent'], inplace=True)
            df['pergunta_proc'] = df['pergunta'].apply(normalize_text)
            log_info(f"CSV carregado: {path}")
            return df
        except Exception as e:
            log_error(f"Erro ao carregar CSV: {e}")
            return pd.DataFrame(columns=['pergunta', 'intent', 'pergunta_proc'])

    def _build_tfidf_model(self):
        if self.perguntas_df.empty: return None, None
        try:
            vectorizer = TfidfVectorizer()
            tfidf_vectors = vectorizer.fit_transform(self.perguntas_df['pergunta_proc'])
            return vectorizer, tfidf_vectors
        except Exception as e:
            log_error(f"Erro ao construir modelo TF-IDF: {e}")
            return None, None

    def _build_bert_model(self, model_name):
        if self.perguntas_df.empty: return None, None
        try:
            m = SentenceTransformer(model_name)
            embs = m.encode(self.perguntas_df['pergunta_proc'].tolist(), convert_to_tensor=True)
            return m, embs
        except Exception as e: log_error(f"Erro BERT: {e}"); return None, None

    def predict_components(self, user_question: str) -> dict:
        norm_question = normalize_text(user_question)
        components = {"intent": Intencao.DESCONHECIDO, "modifiers": {}, "filters": [], "n_top": extract_number(norm_question)}

        if re.search(self.rule_based_patterns["out_of_scope"], norm_question): components["intent"] = Intencao.FORA_DE_ESCOPO; return components
        if re.search(self.rule_based_patterns["distinct"], norm_question): components["modifiers"]["distinct"] = True
        
        for filt in FILTERS_CONFIG:
            match = re.search(filt["regex"], norm_question)
            if match:
                components["filters"].append({"column": filt["db_column"], "value": match.group(1).strip()})

        components["intent"] = self._find_intent_by_similarity(norm_question)

        log_info(f"Componentes Finais: {components}")
        return components

    def _find_intent_by_similarity(self, question_proc: str) -> Intencao:
        if self.perguntas_df.empty: return Intencao.DESCONHECIDO
        best_match_idx, best_score = -1, -1

        # BERT
        if self.embed_model and self.bert_embeddings is not None:
            q_emb = self.embed_model.encode(question_proc, convert_to_tensor=True)
            sims = util.cos_sim(q_emb, self.bert_embeddings)[0]
            idx, score = np.argmax(sims).item(), sims[np.argmax(sims)].item()
            if score > best_score: best_match_idx, best_score = idx, score
        
        # TF-IDF
        if self.vectorizer and self.tfidf_vectors is not None:
            q_vec = self.vectorizer.transform([question_proc])
            sims = cosine_similarity(q_vec, self.tfidf_vectors)[0]
            idx, score = np.argmax(sims).item(), sims[np.argmax(sims)].item()
            if score > best_score: best_match_idx, best_score = idx, score

        # CORREÇÃO: Aumentar o limiar de confiança para evitar falsos positivos.
        if best_match_idx != -1 and best_score > 0.7:
            matched_row = self.perguntas_df.iloc[best_match_idx]
            intent_str = matched_row['intent']
            try: return Intencao[intent_str]
            except KeyError: 
                log_error(f"Intent '{intent_str}' do CSV não é válida.")
                return Intencao.DESCONHECIDO
        
        log_info(f"Confiança de similaridade baixa ({best_score:.2f} <= 0.7). Retornando DESCONHECIDO.")
        return Intencao.DESCONHECIDO
