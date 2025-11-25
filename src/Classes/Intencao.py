from enum import Enum, auto

class Intencao(Enum):
    # Intenções de Agregação Total
    FATURAMENTO_TOTAL = auto()
    TOTAL_ITENS_ESTOQUE = auto()
    TOTAL_PRODUTOS_DISTINTOS = auto()

    # Intenções de Ranking (TOP N)
    TOP_PRODUTOS_ESTOQUE = auto()
    TOP_PRODUTOS_VENDIDOS = auto()
    TOP_CIDADES_FATURAMENTO = auto()
    TOP_CLIENTES_FATURAMENTO = auto()

    # Intenções de Agregação Filtrada
    FATURAMENTO_POR_CIDADE = auto()
    FATURAMENTO_POR_PRODUTO = auto()
    FATURAMENTO_POR_CLIENTE = auto()

    # Nova Intenção de Filtro de Data (Ponto 2.2)
    FILTRO_DATA = auto()

    # Intenções de Controle e Fallback
    PESO_TOTAL_FATURADO = auto() # Alias para FATURAMENTO_TOTAL
    FORA_DE_ESCOPO = auto()
    DESCONHECIDO = auto()
