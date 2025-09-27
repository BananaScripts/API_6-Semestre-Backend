from pydantic import BaseModel
from typing import Optional
from datetime import date

class Venda(BaseModel):
    id_venda: int
    data: date
    cod_cliente: str
    cod_produto: str
    lote: Optional[str]
    origem: Optional[str]
    zs_gr_mercad: Optional[str]
    produto: Optional[str]
    zs_centro: Optional[str]
    zs_cidade: Optional[str]
    zs_uf: Optional[str]
    sku: Optional[str]
    zs_peso_liquido: Optional[float]
    giro_sku_cliente: Optional[float]

class Estoque(BaseModel):
    id_estoque: int
    data: date
    cod_cliente: str
    cod_produto: str
    es_centro: Optional[str]
    tipo_material: Optional[str]
    origem: Optional[str]
    lote: Optional[str]
    dias_em_estoque: Optional[int]
    produto: Optional[str]
    grupo_mercadoria: Optional[str]
    es_totalestoque: Optional[float]
    sku: Optional[str]
