# models.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date
from typing import Optional

# (Opcional, mas recomendado) Função auxiliar para converter snake_case para camelCase
# Isso permite que usemos nomes como "data_nascimento" no Python e "dataNascimento" no JSON/MongoDB
def to_camel(string: str) -> str:
    words = string.split('_')
    return words[0] + ''.join(word.capitalize() for word in words[1:])

# --- Modelos para a Coleção 'clientes' ---

class Visita(BaseModel):
    """Representa uma única visita no histórico de um cliente."""
    data: date
    serviço: str # Pydantic lida bem com o 'ç'

class Cliente(BaseModel):
    """Modelo para a criação de um novo cliente."""
    nome: str
    email: EmailStr
    telefone: str
    data_nascimento: date
    visitas: list[Visita] = []
    ultima_visita: Optional[date] = None
    valor_gasto_total: float = 0.0

    class Config:
        alias_generator = to_camel
        populate_by_name = True # Permite criar o modelo usando nomes em snake_case

class UpdateCliente(BaseModel):
    """Modelo para atualizar um cliente. Todos os campos são opcionais."""
    nome: Optional[str] = None
    telefone: Optional[str] = None
    data_nascimento: Optional[date] = None

    class Config:
        alias_generator = to_camel
        populate_by_name = True

# --- Modelo para a Coleção 'servicos' ---

class Servico(BaseModel):
    """Modelo para criar ou representar um serviço."""
    nome: str
    preco: float = Field(..., gt=0, description="O preço deve ser maior que zero.")
    duracao_minutos: int = Field(..., gt=0, description="A duração deve ser maior que zero.")
    categoria: Optional[str] = None

    class Config:
        alias_generator = to_camel
        populate_by_name = True

# --- Modelo para a Coleção 'agendamentos' ---

class Agendamento(BaseModel):
    """Modelo para a criação de um novo agendamento."""
    cliente_email: EmailStr
    servico: str
    data_hora: datetime
    funcionario: str

    class Config:
        alias_generator = to_camel
        populate_by_name = True

# --- Modelo para a Coleção 'feedbacks' ---

class Feedback(BaseModel):
    """Modelo para a criação de um novo feedback."""
    cliente_email: EmailStr
    servico: str
    nota: int = Field(..., ge=1, le=5, description="A nota deve ser entre 1 e 5.")
    comentario: Optional[str] = None
    data: date

    class Config:
        alias_generator = to_camel
        populate_by_name = True

# --- Modelo para a Coleção 'campanhas' ---

class Campanha(BaseModel):
    """Modelo para a criação de uma nova campanha."""
    nome: str
    descricao: str
    data_inicio: date
    data_fim: date
    segmento: str
    status: str

    class Config:
        alias_generator = to_camel
        populate_by_name = True