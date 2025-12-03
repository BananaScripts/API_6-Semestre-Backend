import spacy
from spacy.pipeline import EntityRuler
import pandas as pd
import numpy as np
import re
import unidecode
from sentence_transformers import SentenceTransformer, util
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .Intencao import Intencao
from .logger import log_info, log_error
from db import get_connection

class NlpEngine:
    def __init__(self, csv_path="../csv/perguntas.csv", embed_model_name="all-MiniLM-L6-v2"):
        log_info("Inicializando NlpEngine Blindada...")
        self.perguntas_df = pd.read_csv(csv_path)
        self._init_intent_models(embed_model_name)
        self._init_spacy_pipeline()

    def _init_intent_models(self, model_name):
        self.embed_model = SentenceTransformer(model_name)
        self.bert_embeddings = self.embed_model.encode(
            self.perguntas_df['pergunta'].tolist(), convert_to_tensor=True
        )
        self.vectorizer = TfidfVectorizer()
        self.tfidf_vectors = self.vectorizer.fit_transform(self.perguntas_df['pergunta'])
        self.CONFIDENCE_THRESHOLD = 0.60 # Baixei um pouco para ser mais permissivo

    def _init_spacy_pipeline(self):
        try:
            self.nlp = spacy.load("pt_core_news_md")
        except OSError:
            from spacy.cli import download
            download("pt_core_news_md")
            self.nlp = spacy.load("pt_core_news_md")

        if "entity_ruler" not in self.nlp.pipe_names:
            ruler = self.nlp.add_pipe("entity_ruler", before="ner")
            
            # Padrões Estáticos
            patterns = [
                {"label": "PRODUTO_SKU", "pattern": [{"TEXT": {"REGEX": "^[A-Z]{2,}-\d{3,4}$"}}]},
                {"label": "CLIENTE_ID", "pattern": [{"LOWER": {"IN": ["cliente", "id", "cod"]}}, {"IS_DIGIT": True}]},
            ]

            # Padrões Dinâmicos (Carregados do Banco)
            db_patterns = self._load_entities_from_db()
            patterns.extend(db_patterns)

            ruler.add_patterns(patterns)

    def _load_entities_from_db(self) -> list:
        patterns = []
        try:
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    # --- CARREGAR CIDADES ---
                    cursor.execute("SELECT DISTINCT zs_cidade FROM domrock.vendas WHERE zs_cidade IS NOT NULL")
                    cidades = {row[0] for row in cursor.fetchall()}
                    
                    for real_name in cidades:
                        # TRUQUE: Divide "São Paulo" em ["São", "Paulo"] para criar tokens separados
                        # Padrão Original
                        tokens_original = [{"LOWER": t.lower()} for t in real_name.split()]
                        patterns.append({"label": "LOC_DB", "pattern": tokens_original, "id": real_name})
                        
                        # Padrão Sem Acento (unidecode)
                        no_acc = unidecode.unidecode(real_name)
                        if no_acc != real_name:
                            tokens_no_acc = [{"LOWER": t.lower()} for t in no_acc.split()]
                            patterns.append({"label": "LOC_DB", "pattern": tokens_no_acc, "id": real_name})

                    # --- CARREGAR PRODUTOS ---
                    cursor.execute("SELECT DISTINCT produto FROM domrock.vendas WHERE produto IS NOT NULL")
                    produtos = {row[0] for row in cursor.fetchall()}
                    
                    for real_prod in produtos:
                        tokens_prod = [{"LOWER": t.lower()} for t in real_prod.split()]
                        patterns.append({"label": "PRODUTO_DB", "pattern": tokens_prod, "id": real_prod})
                        
                        no_acc_prod = unidecode.unidecode(real_prod)
                        if no_acc_prod != real_prod:
                            tokens_no_acc_prod = [{"LOWER": t.lower()} for t in no_acc_prod.split()]
                            patterns.append({"label": "PRODUTO_DB", "pattern": tokens_no_acc_prod, "id": real_prod})

        except Exception as e:
            log_error(f"Erro ao carregar entidades: {e}")
        
        return patterns

    def extract_entities(self, text: str) -> list:
        doc = self.nlp(text)
        filters = []
        
        # === ETAPA 1: Processa as Entidades (spacy + regras + regex) ===
        for ent in doc.ents:
            # 1. Match Exato do Banco
            if ent.label_ == "PRODUTO_DB":
                filters.append({"type": "produto", "column": "produto", "value": ent.ent_id_})
            elif ent.label_ == "LOC_DB":
                filters.append({"type": "cidade", "column": "zs_cidade", "value": ent.ent_id_})
            
            # 2. Padrões Regex (SKU/Cliente)
            elif ent.label_ == "PRODUTO_SKU":
                filters.append({"type": "produto", "column": "sku", "value": ent.text})
            elif ent.label_ == "CLIENTE_ID":
                nums = [t.text for t in ent if t.is_digit]
                if nums: filters.append({"type": "cliente", "column": "cod_cliente", "value": nums[0]})

            # 3. Fallback Genérico para Cidades
            elif ent.label_ in ["LOC", "GPE"] and "cidade" not in [f['type'] for f in filters]:
                raw_val = ent.text
                trash_prefixes = ["na ", "no ", "em ", "de ", "do ", "da ", "para ", "a ", "o ", "as ", "os ", "cidade ", "municipio ", "estado "]
                clean_val = raw_val.strip()
                while True:
                    original_val = clean_val
                    for prefix in trash_prefixes:
                        if clean_val.lower().startswith(prefix):
                            clean_val = clean_val[len(prefix):].strip()
                    if clean_val == original_val: break
                
                filters.append({"type": "cidade", "column": "zs_cidade", "value": clean_val})

        # === ETAPA 2: Fallback para Produtos Desconhecidos ===
        
        has_product = any(f['type'] == 'produto' for f in filters)
        
        if not has_product:
            # Captura tudo depois de "estoque de", "venda de", "produto"
            match = re.search(r'(?:estoque|vendas?|faturamento|produto)\s+(?:de|do|da|dos|das|para)\s+(.+)', text, re.IGNORECASE)
            
            if match:
                candidate = match.group(1).strip().replace("?", "")
                
                # === CORREÇÃO AQUI ===
                # Verifica se esse "candidato a produto" não é na verdade um cliente ou cidade que JÁ achamos.
                # Ex: se achamos cliente '10179', e o candidato é 'cliente 10179', isso é redundante.
                is_redundant = False
                for f in filters:
                    # Se o valor do filtro (ex: "10179") está dentro do texto candidato (ex: "cliente 10179")
                    if str(f['value']).lower() in candidate.lower():
                        is_redundant = True
                        break
                
                # Só adiciona se NÃO for redundante
                if not is_redundant and len(candidate) > 1:
                    filters.append({"type": "produto", "column": "produto", "value": candidate})

        return filters

    def _extract_number(self, text: str) -> int:
        match = re.search(r'\b(\d+)\b', text)
        return int(match.group(1)) if match else 5

    def predict_components(self, user_question: str) -> dict:
            components = {"intent": Intencao.DESCONHECIDO, "filters": [], "n_top": 5}
            
            # 1. Extração de Entidades e Números
            components["filters"] = self.extract_entities(user_question)
            components["n_top"] = self._extract_number(user_question)
            
            # 2. Classificação Padrão (BERT + TFIDF)
            q_emb = self.embed_model.encode(user_question, convert_to_tensor=True)
            bert_sims = util.cos_sim(q_emb, self.bert_embeddings)[0].cpu().numpy()
            q_vec = self.vectorizer.transform([user_question])
            tfidf_sims = cosine_similarity(q_vec, self.tfidf_vectors)[0]
            
            combined_sims = (bert_sims * 0.7) + (tfidf_sims * 0.3)
            best_idx = np.argmax(combined_sims)
            
            # Define a intenção baseada na IA
            if combined_sims[best_idx] > self.CONFIDENCE_THRESHOLD:
                intent_str = self.perguntas_df.iloc[best_idx]['intent']
                components["intent"] = Intencao[intent_str]
            
            # ====================================================================
            # 3. REGRAS DE DESEMPATE (AQUI CORRIGIMOS O "TOP 3 PRODUTOS")
            # ====================================================================
            
            text = user_question.lower()
            
            # Se for uma pergunta de RANKING (tem "top", "mais", "maiores" ou número detectado)
            is_ranking = "top" in text or "mais" in text or "maior" in text or "melhor" in text
            
            if is_ranking:
                # Se falou "produto", "mercadoria", "item" -> Força Produto
                if any(w in text for w in ["produto", "mercadoria", "item", "itens"]):
                    if "estoque" in text:
                        components["intent"] = Intencao.TOP_PRODUTOS_ESTOQUE
                    else:
                        # Assume "Vendidos/Faturados" se não falou estoque
                        components["intent"] = Intencao.TOP_PRODUTOS_VENDIDOS
                
                # Se falou "cliente" -> Força Cliente
                elif "cliente" in text:
                    components["intent"] = Intencao.TOP_CLIENTES_FATURAMENTO
                    
                # Se falou "cidade" -> Força Cidade
                elif "cidade" in text or "regiao" in text:
                    components["intent"] = Intencao.TOP_CIDADES_FATURAMENTO
        
            elif components["intent"] == Intencao.DESCONHECIDO and len(components["filters"]) > 0:
                types = [f['type'] for f in components['filters']]
                if 'cidade' in types: components["intent"] = Intencao.FATURAMENTO_POR_CIDADE
                elif 'produto' in types: components["intent"] = Intencao.FATURAMENTO_POR_PRODUTO
                elif 'cliente' in types: components["intent"] = Intencao.FATURAMENTO_POR_CLIENTE

            return components