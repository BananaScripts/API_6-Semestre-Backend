
from enum import Enum

class Intencao(Enum):
    # === Intenções de Negócio ===
    TOTAL_ITENS_ESTOQUE = "TOTAL_ITENS_ESTOQUE"          # Quantidade total de itens no estoque
    TOTAL_PRODUTOS_DISTINTOS = "TOTAL_PRODUTOS_DISTINTOS"  # Contagem de SKUs únicos
    PESO_TOTAL_FATURADO = "PESO_TOTAL_FATURADO"          # Soma do peso líquido vendido
    TOP_PRODUTOS_ESTOQUE = "TOP_PRODUTOS_ESTOQUE"        # Ranking de produtos por quantidade em estoque
    TOP_CIDADES_FATURAMENTO = "TOP_CIDADES_FATURAMENTO"     # Ranking de cidades por peso vendido
    FATURAMENTO_TOTAL = "FATURAMENTO_TOTAL"              # Alias para PESO_TOTAL_FATURADO
    TOP_CLIENTES_FATURAMENTO = "TOP_CLIENTES_FATURAMENTO" # Ranking de clientes por peso vendido

    # === Intenções de Sistema ===
    DESCONHECIDO = "DESCONHECIDO"                        # A PNL não conseguiu identificar a intenção
    FORA_DE_ESCOPO = "FORA_DE_ESCOPO"                    # A pergunta é válida, mas não pode ser respondida
