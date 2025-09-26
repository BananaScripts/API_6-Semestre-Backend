from enum import Enum

class Upload(str, Enum):
    vendas = "vendas"
    estoque = "estoque"