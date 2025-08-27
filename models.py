# models.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date
from typing import Optional

# Função auxiliar para converter snake_case para camelCase
def to_camel(string: str) -> str:
    words = string.split('_')
    return words[0] + ''.join(word.capitalize() for word in words[1:])

# --- Modelos para a Coleção 'clientes' ---

class Visita(BaseModel):
    data: date
    serviço: str

class Cliente(BaseModel):
    nome: str
    email: EmailStr
    telefone: str
    data_nascimento: date
    visitas: list[Visita] = []
    ultima_visita: Optional[date] = None
    valor_gasto_total: float = 0.0

    class Config:
        alias_generator = to_camel
        populate_by_name = True

class UpdateCliente(BaseModel):
    nome: Optional[str] = None
    telefone: Optional[str] = None
    data_nascimento: Optional[date] = None

    class Config:
        alias_generator = to_camel
        populate_by_name = True

# --- Modelos para a Coleção 'servicos' ---

class Servico(BaseModel):
    nome: str
    preco: float = Field(..., gt=0)
    duracao_minutos: int = Field(..., gt=0)
    categoria: Optional[str] = None

    class Config:
        alias_generator = to_camel
        populate_by_name = True

# --- Modelo para ATUALIZAR um serviço ---
class UpdateServico(BaseModel):
    nome: Optional[str] = None
    preco: Optional[float] = Field(None, gt=0)
    duracao_minutos: Optional[int] = Field(None, gt=0)
    categoria: Optional[str] = None
    
    class Config:
        alias_generator = to_camel
        populate_by_name = True

# --- Modelo para a Coleção 'agendamentos' ---

class Agendamento(BaseModel):
    cliente_email: EmailStr
    servico: str
    data_hora: datetime
    funcionario: str

    class Config:
        alias_generator = to_camel
        populate_by_name = True

# --- Modelo para a Coleção 'feedbacks' ---

class Feedback(BaseModel):
    cliente_email: EmailStr
    servico: str
    nota: int = Field(..., ge=1, le=5)
    comentario: Optional[str] = None
    data: date

    class Config:
        alias_generator = to_camel
        populate_by_name = True

# --- Modelo para a Coleção 'campanhas' ---

class Campanha(BaseModel):
    nome: str
    descricao: str
    data_inicio: date
    data_fim: date
    segmento: str
    status: str

    class Config:
        alias_generator = to_camel
        populate_by_name = True

# --- Modelo para ATUALIZAR uma campanha ---
class UpdateCampanha(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    segmento: Optional[str] = None
    status: Optional[str] = None

    class Config:
        alias_generator = to_camel
        populate_by_name = True