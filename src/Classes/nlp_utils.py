import re
import numpy as np
import pandas as pd
import unidecode
import torch
from sentence_transformers import SentenceTransformer, util
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta
from .Intencao import Intencao
from .logger import log_info, log_error

def normalize_text(text: str) -> str:
    if not text: return ""
    text = text.lower()
    text = unidecode.unidecode(text)
    text = re.sub(r'[^a-z0-9\s/]', '', text).strip()
    return re.sub(r'\s+', ' ', text)

def extract_number(text: str, default: int = 5) -> int:
    nums = re.findall(r'\d+', text)
    return int(nums[0]) if nums else default

def extract_date_range(norm_text: str) -> dict | None:
    today = datetime.now().date()
    if "hoje" in norm_text: return {"start_date": today.strftime("%Y-%m-%d"), "end_date": today.strftime("%Y-%m-%d")}
    if "ontem" in norm_text:
        yesterday = today - timedelta(days=1)
        return {"start_date": yesterday.strftime("%Y-%m-%d"), "end_date": yesterday.strftime("%Y-%m-%d")}
    if "semana passada" in norm_text:
        last_week_end = today - timedelta(days=today.weekday() + 1)
        last_week_start = last_week_end - timedelta(days=6)
        return {"start_date": last_week_start.strftime("%Y-%m-%d"), "end_date": last_week_end.strftime("%Y-%m-%d")}
    if "mes passado" in norm_text:
        first_day_current_month = today.replace(day=1)
        last_day_last_month = first_day_current_month - timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)
        return {"start_date": first_day_last_month.strftime("%Y-%m-%d"), "end_date": last_day_last_month.strftime("%Y-%m-%d")}
    match = re.search(r"(?:entre|de)\s+(\d{2}/\d{2}/\d{2,4})\s+(?:a|e)\s+(\d{2}/\d{2}/\d{2,4})", norm_text)
    if match:
        start_str, end_str = match.groups()
        fmt = "%d/%m/%Y" if len(start_str.split('/')[2]) == 4 else "%d/%m/%y"
        try:
            start_date = datetime.strptime(start_str, fmt).date()
            end_date = datetime.strptime(end_str, fmt).date()
            return {"start_date": start_date.strftime("%Y-%m-%d"), "end_date": end_date.strftime("%Y-%m-%d")}
        except ValueError: pass
    return None

FILTERS_CONFIG = [
    {"type": "cliente", "regex": r"(?:do\s+cliente|para\s+o\s+cliente|cliente)\s+([0-9]+)(?=\s+e\s|$)", "db_column": "cod_cliente"},
    {"type": "cidade", "regex": r"(?:na\s+cidade\s+de|da\s+cidade\s+de|para\s+a\s+cidade\s+de|cidade\s+de|na\s+cidade|cidade)\s+([a-zA-Z\s]+?)(?=\s+e\s|\s+do\s|\s+com\s|$)", "db_column": "zs_cidade"},
    {"type": "produto", "regex": r"(?:do\s+produto|para\s+o\s+produto|produto|do|da|de)\s+([a-zA-Z0-9-]+)(?=\s|$)", "db_column": "produto"},
]

STOPWORDS = {
    # Artigos
    "a", "o", "as", "os", "um", "uma", "uns", "umas",
    # Preposições
    "de", "da", "do", "das", "dos", "em", "no", "na", "nos", "nas", "por", "para", "com", "sem", "sob", "sobre",
    # Conjunções
    "e", "ou", "mas", "se", "porque", "que", "quando", "como",
    # Advérbios comuns
    "mais", "muito", "ja", "ainda", "ontem", "hoje", "amanha",
    # Verbos comuns
    "é", "sao", "foi", "era", "estava", "tem", "tinha", "ter", "ha", "houve",
    # Palavras-chave do domínio que não devem ser filtros
    "itens", "total", "faturamento", "vendas", "valor", "cidade", "produto", "cliente", "clientes", "estoque"
}

class NlpEngine:
    def __init__(self, csv_path="../csv/perguntas.csv", embed_model_name="all-MiniLM-L6-v2"):
        log_info("Inicializando NlpEngine com sistema de score Híbrido e Stopwords...")
        self.perguntas_df = self._load_and_process_csv(csv_path)
        self.vectorizer, self.tfidf_vectors = self._build_tfidf_model()
        self.embed_model, self.bert_embeddings = self._build_bert_model(embed_model_name)
        self.rule_based_patterns = {
            "out_of_scope": r"(nao faturado|cancelado|devolvido)",
            "distinct": r"(distintos|diferentes|unicos)",
        }
        self.CONFIDENCE_THRESHOLD = 0.68
        self.FALLBACK_THRESHOLD = 0.58 
        log_info("NlpEngine Híbrida inicializada e pronta.")

    def _load_and_process_csv(self, path):
        try:
            df = pd.read_csv(path)
            df.dropna(subset=['pergunta', 'intent'], inplace=True)
            log_info(f"{len(df.index)} perguntas carregadas e processadas do CSV.")
            df['pergunta_proc'] = df['pergunta'].apply(normalize_text)
            return df
        except Exception as e: log_error(f"Erro crítico ao carregar/processar CSV: {e}"); return pd.DataFrame()

    def _build_tfidf_model(self):
        if self.perguntas_df.empty: return None, None
        try: vectorizer = TfidfVectorizer(); tfidf_vectors = vectorizer.fit_transform(self.perguntas_df['pergunta_proc']); return vectorizer, tfidf_vectors
        except Exception as e: log_error(f"Erro ao construir modelo TF-IDF: {e}"); return None, None

    def _build_bert_model(self, model_name):
        if self.perguntas_df.empty: return None, None
        try: m = SentenceTransformer(model_name); embs = m.encode(self.perguntas_df['pergunta_proc'].tolist(), convert_to_tensor=True); return m, embs
        except Exception as e: log_error(f"Erro crítico ao carregar modelo BERT: {e}"); return None, None

    def predict_components(self, user_question: str) -> dict:
        raw_question = user_question.lower()
        norm_question = normalize_text(raw_question)
        
        components = {"intent": Intencao.DESCONHECIDO, "modifiers": {}, "filters": [], "n_top": extract_number(norm_question)}

        if re.search(self.rule_based_patterns["out_of_scope"], norm_question): components["intent"] = Intencao.FORA_DE_ESCOPO; return components
        if re.search(self.rule_based_patterns["distinct"], norm_question): components["modifiers"]["distinct"] = True

        date_range = extract_date_range(raw_question)
        if date_range:
            components["filters"].append({"type": "date_range", "value": date_range})

        for filt_config in FILTERS_CONFIG:
            match = re.search(filt_config["regex"], norm_question)
            if match:
                value = match.group(1).strip()
                value_words = set(value.split())
                if not value_words.isdisjoint(STOPWORDS):
                    continue
                
                if filt_config['type'] == 'produto' and any(f.get('type') == 'cidade' and value in f['value'] for f in components['filters']):
                    continue
                
                components["filters"].append({"type": filt_config["type"], "column": filt_config["db_column"], "value": value})

        intent, score = self._find_intent_by_similarity(norm_question)
        components["intent"] = intent

        if intent == Intencao.FILTRO_DATA and len(components["filters"]) > 1:
            components["intent"] = Intencao.FATURAMENTO_TOTAL

        log_info(f"Componentes Finais: {components} (Score: {score:.4f})")
        return components

    def _find_intent_by_similarity(self, question_proc: str, allowed_intents: list = None) -> tuple[Intencao, float]:
        if not question_proc or self.perguntas_df.empty: return Intencao.DESCONHECIDO, 0.0

        df = self.perguntas_df
        bert_embeddings = self.bert_embeddings
        tfidf_vectors = self.tfidf_vectors
        
        q_emb = self.embed_model.encode(question_proc, convert_to_tensor=True)
        bert_sims = util.cos_sim(q_emb, bert_embeddings)[0]
        bert_score = torch.max(bert_sims).item()

        q_vec = self.vectorizer.transform([question_proc])
        tfidf_sims = cosine_similarity(q_vec, tfidf_vectors)[0]
        tfidf_score = np.max(tfidf_sims)

        combined_score = (bert_score * 0.8) + (float(tfidf_score) * 0.2)
        
        if combined_score > self.CONFIDENCE_THRESHOLD:
            best_match_idx = torch.argmax(bert_sims).item() if bert_score >= tfidf_score else np.argmax(tfidf_sims).item()
        elif combined_score > self.FALLBACK_THRESHOLD:
            log_info(f"Usando Fallback de Embeddings. Score: {combined_score:.4f}")
            best_match_idx = torch.argmax(bert_sims).item()
        else:
            return Intencao.DESCONHECIDO, combined_score

        original_index = df.index[best_match_idx]
        matched_row = self.perguntas_df.loc[original_index]
        intent_str = matched_row['intent']
        try: return Intencao[intent_str], combined_score
        except KeyError: log_error(f"Intent '{intent_str}' do CSV não é válida."); return Intencao.DESCONHECIDO, combined_score
