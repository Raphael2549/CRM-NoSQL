from fastapi import FastAPI
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from typing import Optional
from datetime import datetime
from datetime import datetime, timedelta
import random
from contextlib import asynccontextmanager
from collections import Counter
import os

mongo_uri = os.getenv("MONGODB_URI")

client = MongoClient(mongo_uri, server_api=ServerApi('1'))

db = client["CRM_Salão"]

clientes = db["clientes"]

# Dados de exemplo
clientes_exemplos = [
    {
        "nome": "Fernanda Lima",
        "email": "fernanda.lima1@email.com",
        "telefone": "11910000001",
        "dataNascimento": "1987-04-10",
        "visitas": [
            {"data": "2025-08-01", "serviço": "manicure"},
            {"data": "2025-07-15", "serviço": "escova"}
        ],
        "ultimaVisita": "2025-08-01",
        "valorGastoTotal": 720.00
    },
    {
        "nome": "Lucas Souza",
        "email": "lucas.souza2@email.com",
        "telefone": "11910000002",
        "dataNascimento": "1991-09-21",
        "visitas": [
            {"data": "2025-07-20", "serviço": "hidratação"},
            {"data": "2025-06-30", "serviço": "pintura de cabelo"}
        ],
        "ultimaVisita": "2025-07-20",
        "valorGastoTotal": 890.00
    },
    {
        "nome": "Camila Ferreira",
        "email": "camila.ferreira3@email.com",
        "telefone": "11910000003",
        "dataNascimento": "1990-02-11",
        "visitas": [
            {"data": "2025-07-25", "serviço": "escova"},
            {"data": "2025-07-05", "serviço": "manicure"}
        ],
        "ultimaVisita": "2025-07-25",
        "valorGastoTotal": 450.00
    },
    {
        "nome": "Bruno Santos",
        "email": "bruno.santos4@email.com",
        "telefone": "11910000004",
        "dataNascimento": "1985-07-19",
        "visitas": [
            {"data": "2025-07-18", "serviço": "corte"},
            {"data": "2025-06-10", "serviço": "hidratação"}
        ],
        "ultimaVisita": "2025-07-18",
        "valorGastoTotal": 630.00
    },
    {
        "nome": "Juliana Almeida",
        "email": "juliana.almeida5@email.com",
        "telefone": "11910000005",
        "dataNascimento": "1993-12-02",
        "visitas": [
            {"data": "2025-07-22", "serviço": "manicure"},
            {"data": "2025-06-25", "serviço": "pintura de cabelo"}
        ],
        "ultimaVisita": "2025-07-22",
        "valorGastoTotal": 710.00
    },
    {
        "nome": "Ricardo Oliveira",
        "email": "ricardo.oliveira6@email.com",
        "telefone": "11910000006",
        "dataNascimento": "1988-11-30",
        "visitas": [
            {"data": "2025-07-20", "serviço": "hidratação"},
            {"data": "2025-07-01", "serviço": "escova"}
        ],
        "ultimaVisita": "2025-07-20",
        "valorGastoTotal": 550.00
    },
    {
        "nome": "Patrícia Costa",
        "email": "patricia.costa7@email.com",
        "telefone": "11910000007",
        "dataNascimento": "1984-03-14",
        "visitas": [
            {"data": "2025-07-28", "serviço": "corte"},
            {"data": "2025-06-28", "serviço": "manicure"}
        ],
        "ultimaVisita": "2025-07-28",
        "valorGastoTotal": 900.00
    },
    {
        "nome": "Thiago Martins",
        "email": "thiago.martins8@email.com",
        "telefone": "11910000008",
        "dataNascimento": "1986-05-07",
        "visitas": [
            {"data": "2025-07-15", "serviço": "pintura de cabelo"},
            {"data": "2025-07-03", "serviço": "hidratação"}
        ],
        "ultimaVisita": "2025-07-15",
        "valorGastoTotal": 820.00
    },
    {
        "nome": "Carla Nunes",
        "email": "carla.nunes9@email.com",
        "telefone": "11910000009",
        "dataNascimento": "1992-08-23",
        "visitas": [
            {"data": "2025-07-19", "serviço": "manicure"},
            {"data": "2025-06-29", "serviço": "escova"}
        ],
        "ultimaVisita": "2025-07-19",
        "valorGastoTotal": 610.00
    },
    {
        "nome": "Diego Ribeiro",
        "email": "diego.ribeiro10@email.com",
        "telefone": "11910000010",
        "dataNascimento": "1989-01-30",
        "visitas": [
            {"data": "2025-07-21", "serviço": "corte"},
            {"data": "2025-06-30", "serviço": "hidratação"}
        ],
        "ultimaVisita": "2025-07-21",
        "valorGastoTotal": 750.00
    },
    {
        "nome": "Isabela Moreira",
        "email": "isabela.moreira11@email.com",
        "telefone": "11910000011",
        "dataNascimento": "1987-06-15",
        "visitas": [
            {"data": "2025-07-18", "serviço": "manicure"},
            {"data": "2025-07-01", "serviço": "pintura de cabelo"}
        ],
        "ultimaVisita": "2025-07-18",
        "valorGastoTotal": 680.00
    },
    {
        "nome": "Marcos Lima",
        "email": "marcos.lima12@email.com",
        "telefone": "11910000012",
        "dataNascimento": "1990-10-12",
        "visitas": [
            {"data": "2025-07-23", "serviço": "escova"},
            {"data": "2025-07-03", "serviço": "hidratação"}
        ],
        "ultimaVisita": "2025-07-23",
        "valorGastoTotal": 540.00
    },
    {
        "nome": "Natalia Santos",
        "email": "natalia.santos13@email.com",
        "telefone": "11910000013",
        "dataNascimento": "1985-09-27",
        "visitas": [
            {"data": "2025-07-26", "serviço": "corte"},
            {"data": "2025-07-05", "serviço": "manicure"}
        ],
        "ultimaVisita": "2025-07-26",
        "valorGastoTotal": 880.00
    },
    {
        "nome": "Paulo Almeida",
        "email": "paulo.almeida14@email.com",
        "telefone": "11910000014",
        "dataNascimento": "1988-02-08",
        "visitas": [
            {"data": "2025-07-17", "serviço": "pintura de cabelo"},
            {"data": "2025-06-28", "serviço": "escova"}
        ],
        "ultimaVisita": "2025-07-17",
        "valorGastoTotal": 790.00
    },
    {
        "nome": "Renata Ferreira",
        "email": "renata.ferreira15@email.com",
        "telefone": "11910000015",
        "dataNascimento": "1991-11-11",
        "visitas": [
            {"data": "2025-07-20", "serviço": "hidratação"},
            {"data": "2025-07-02", "serviço": "manicure"}
        ],
        "ultimaVisita": "2025-07-20",
        "valorGastoTotal": 670.00
    },
    {
        "nome": "Sandro Gomes",
        "email": "sandro.gomes16@email.com",
        "telefone": "11910000016",
        "dataNascimento": "1984-07-03",
        "visitas": [
            {"data": "2025-07-22", "serviço": "corte"},
            {"data": "2025-07-06", "serviço": "pintura de cabelo"}
        ],
        "ultimaVisita": "2025-07-22",
        "valorGastoTotal": 830.00
    },
    {
        "nome": "Tatiana Rocha",
        "email": "tatiana.rocha17@email.com",
        "telefone": "11910000017",
        "dataNascimento": "1989-04-19",
        "visitas": [
            {"data": "2025-07-24", "serviço": "manicure"},
            {"data": "2025-07-04", "serviço": "escova"}
        ],
        "ultimaVisita": "2025-07-24",
        "valorGastoTotal": 610.00
    },
    {
        "nome": "Vitor Carvalho",
        "email": "vitor.carvalho18@email.com",
        "telefone": "11910000018",
        "dataNascimento": "1993-01-05",
        "visitas": [
            {"data": "2025-07-21", "serviço": "hidratação"},
            {"data": "2025-07-02", "serviço": "pintura de cabelo"}
        ],
        "ultimaVisita": "2025-07-21",
        "valorGastoTotal": 740.00
    }
]

servicos_exemplos = [
    {"nome": "Corte de cabelo", "preco": 120.00, "duracaoMinutos": 45},
    {"nome": "Hidratação", "preco": 80.00, "duracaoMinutos": 30},
    {"nome": "Manicure", "preco": 50.00, "duracaoMinutos": 40},
    {"nome": "Pintura de cabelo", "preco": 200.00, "duracaoMinutos": 90},
    {"nome": "Escova", "preco": 100.00, "duracaoMinutos": 60},
    {"nome": "Spa capilar", "preco": 150.00, "duracaoMinutos": 70},
    {"nome": "Tratamento antiqueda", "preco": 180.00, "duracaoMinutos": 60},
    {"nome": "Massagem relaxante", "preco": 120.00, "duracaoMinutos": 50},
    {"nome": "Alongamento de unhas", "preco": 90.00, "duracaoMinutos": 80},
    {"nome": "Design de sobrancelhas", "preco": 70.00, "duracaoMinutos": 30},
    {"nome": "Limpeza de pele", "preco": 110.00, "duracaoMinutos": 45},
    {"nome": "Coloração de sobrancelhas", "preco": 60.00, "duracaoMinutos": 25},
    {"nome": "Depilação facial", "preco": 75.00, "duracaoMinutos": 30},
    {"nome": "Tratamento capilar noturno", "preco": 130.00, "duracaoMinutos": 40},
    {"nome": "Maquiagem para eventos", "preco": 160.00, "duracaoMinutos": 90},
    {"nome": "Penteado para festas", "preco": 140.00, "duracaoMinutos": 60},
    {"nome": "Escova progressiva", "preco": 250.00, "duracaoMinutos": 120},
    {"nome": "Tratamento para couro cabeludo", "preco": 110.00, "duracaoMinutos": 50},
    {"nome": "Manicure express", "preco": 40.00, "duracaoMinutos": 25},
    {"nome": "Banho de brilho", "preco": 90.00, "duracaoMinutos": 35}
]

campanhas_exemplos = [
    {
        "nome": "Outono 2025",
        "descricao": "Desconto de 10% em corte para novos clientes",
        "dataInicio": "2025-09-01",
        "dataFim": "2025-11-30",
        "segmento": "novos clientes",
        "status": "ativa"
    },
    {
        "nome": "Promoção Especial",
        "descricao": "Pacote manicure + hidratação com 15% de desconto",
        "dataInicio": "2025-08-15",
        "dataFim": "2025-09-15",
        "segmento": "todos os clientes",
        "status": "ativa"
    },
    {
        "nome": "Black November",
        "descricao": "Descontos progressivos em todos os serviços",
        "dataInicio": "2025-11-01",
        "dataFim": "2025-11-30",
        "segmento": "todos os clientes",
        "status": "planejada"
    },
    {
        "nome": "Natal 2025",
        "descricao": "Kits especiais para presentear",
        "dataInicio": "2025-12-01",
        "dataFim": "2025-12-31",
        "segmento": "clientes VIP",
        "status": "planejada"
    },
    {
        "nome": "Verão 2026",
        "descricao": "Descontos em tratamentos capilares para o verão",
        "dataInicio": "2026-01-01",
        "dataFim": "2026-03-31",
        "segmento": "todos os clientes",
        "status": "planejada"
    },
    {
        "nome": "Semana da Beleza",
        "descricao": "Promoções em manicure e pedicure",
        "dataInicio": "2025-08-10",
        "dataFim": "2025-08-17",
        "segmento": "todos os clientes",
        "status": "ativa"
    },
    {
        "nome": "Dia da Mulher",
        "descricao": "Descontos especiais em cortes e tratamentos",
        "dataInicio": "2025-03-01",
        "dataFim": "2025-03-08",
        "segmento": "mulheres",
        "status": "ativa"
    },
    {
        "nome": "Aniversário do Salão 2025",
        "descricao": "Descontos e brindes para clientes frequentes",
        "dataInicio": "2025-08-01",
        "dataFim": "2025-08-31",
        "segmento": "clientes frequentes",
        "status": "ativa"
    },
    {
        "nome": "Promoção de Inverno",
        "descricao": "Descontos em hidratação e spa capilar",
        "dataInicio": "2025-06-01",
        "dataFim": "2025-08-31",
        "segmento": "todos os clientes",
        "status": "inativa"
    },
    {
        "nome": "Semana da Noiva",
        "descricao": "Pacotes especiais para noivas e madrinhas",
        "dataInicio": "2025-09-15",
        "dataFim": "2025-09-22",
        "segmento": "noivas",
        "status": "planejada"
    },
    {
        "nome": "Promoção de Volta às Aulas",
        "descricao": "Descontos para estudantes",
        "dataInicio": "2025-01-10",
        "dataFim": "2025-02-28",
        "segmento": "estudantes",
        "status": "ativa"
    },
    {
        "nome": "Promoção Exclusiva VIP",
        "descricao": "Descontos para clientes VIP em todos os serviços",
        "dataInicio": "2025-07-01",
        "dataFim": "2025-07-31",
        "segmento": "clientes VIP",
        "status": "ativa"
    },
    {
        "nome": "Festival de Cores",
        "descricao": "Descontos em pintura e coloração",
        "dataInicio": "2025-10-01",
        "dataFim": "2025-10-15",
        "segmento": "todos os clientes",
        "status": "planejada"
    },
    {
        "nome": "Férias 2025",
        "descricao": "Pacotes promocionais para tratamentos de cabelo",
        "dataInicio": "2025-12-01",
        "dataFim": "2026-01-15",
        "segmento": "todos os clientes",
        "status": "planejada"
    },
    {
        "nome": "Semana da Saúde Capilar",
        "descricao": "Descontos em tratamentos específicos para couro cabeludo",
        "dataInicio": "2025-07-20",
        "dataFim": "2025-07-27",
        "segmento": "todos os clientes",
        "status": "ativa"
    }
]

feedbacks_exemplos = [
    {
        "cliente_email": "fernanda.lima1@email.com",
        "servico": "manicure",
        "nota": 5,
        "comentario": "Serviço impecável, adorei!",
        "data": "2025-08-02"
    },
    {
        "cliente_email": "lucas.souza2@email.com",
        "servico": "hidratação",
        "nota": 4,
        "comentario": "Muito bom, cabelo ficou ótimo.",
        "data": "2025-07-21"
    },
    {
        "cliente_email": "camila.ferreira3@email.com",
        "servico": "escova",
        "nota": 5,
        "comentario": "Profissionais super atenciosos.",
        "data": "2025-07-26"
    },
    {
        "cliente_email": "bruno.santos4@email.com",
        "servico": "corte",
        "nota": 3,
        "comentario": "Corte bom, mas demorou mais que o esperado.",
        "data": "2025-07-19"
    },
    {
        "cliente_email": "juliana.almeida5@email.com",
        "servico": "manicure",
        "nota": 4,
        "comentario": "Gostei bastante do resultado.",
        "data": "2025-07-23"
    },
    {
        "cliente_email": "ricardo.oliveira6@email.com",
        "servico": "hidratação",
        "nota": 5,
        "comentario": "Meu cabelo ficou renovado!",
        "data": "2025-07-21"
    },
    {
        "cliente_email": "patricia.costa7@email.com",
        "servico": "corte",
        "nota": 5,
        "comentario": "Atendimento excelente e corte perfeito.",
        "data": "2025-07-29"
    },
    {
        "cliente_email": "thiago.martins8@email.com",
        "servico": "pintura de cabelo",
        "nota": 4,
        "comentario": "Gostei muito da cor e do atendimento.",
        "data": "2025-07-16"
    },
    {
        "cliente_email": "carla.nunes9@email.com",
        "servico": "manicure",
        "nota": 3,
        "comentario": "Serviço bom, poderia ser mais rápido.",
        "data": "2025-07-20"
    },
    {
        "cliente_email": "diego.ribeiro10@email.com",
        "servico": "corte",
        "nota": 5,
        "comentario": "Corte perfeito e rápido.",
        "data": "2025-07-22"
    },
    {
        "cliente_email": "isabela.moreira11@email.com",
        "servico": "manicure",
        "nota": 4,
        "comentario": "Gostei, bom custo-benefício.",
        "data": "2025-07-19"
    },
    {
        "cliente_email": "marcos.lima12@email.com",
        "servico": "escova",
        "nota": 5,
        "comentario": "Cabelo ficou lindo, adorei!",
        "data": "2025-07-24"
    },
    {
        "cliente_email": "natalia.santos13@email.com",
        "servico": "corte",
        "nota": 4,
        "comentario": "Muito bom, recomendo.",
        "data": "2025-07-27"
    },
    {
        "cliente_email": "paulo.almeida14@email.com",
        "servico": "pintura de cabelo",
        "nota": 3,
        "comentario": "Gostei da cor, mas achei caro.",
        "data": "2025-07-18"
    },
    {
        "cliente_email": "renata.ferreira15@email.com",
        "servico": "hidratação",
        "nota": 5,
        "comentario": "Meu cabelo nunca esteve tão hidratado!",
        "data": "2025-07-21"
    },
    {
        "cliente_email": "sandro.gomes16@email.com",
        "servico": "corte",
        "nota": 4,
        "comentario": "Atendimento excelente.",
        "data": "2025-07-23"
    },
    {
        "cliente_email": "tatiana.rocha17@email.com",
        "servico": "manicure",
        "nota": 3,
        "comentario": "Demorou, mas ficou bom.",
        "data": "2025-07-25"
    },
    {
        "cliente_email": "vitor.carvalho18@email.com",
        "servico": "hidratação",
        "nota": 5,
        "comentario": "Recomendo a todos!",
        "data": "2025-07-22"
    },
    {
        "cliente_email": "fernanda.lima1@email.com",
        "servico": "escova",
        "nota": 4,
        "comentario": "Gostei do resultado.",
        "data": "2025-08-03"
    },
    {
        "cliente_email": "lucas.souza2@email.com",
        "servico": "manicure",
        "nota": 5,
        "comentario": "Serviço de qualidade.",
        "data": "2025-07-22"
    }
]

agendamentos_exemplos = [
    {
        "cliente_email": "fernanda.lima1@email.com",
        "servico": "manicure",
        "dataHora": "2025-08-10T15:00:00",
        "funcionario": "Ana",
        "status": "confirmado"
    },
    {
        "cliente_email": "lucas.souza2@email.com",
        "servico": "hidratação",
        "dataHora": "2025-08-11T10:00:00",
        "funcionario": "Bianca",
        "status": "confirmado"
    },
    {
        "cliente_email": "camila.ferreira3@email.com",
        "servico": "escova",
        "dataHora": "2025-08-12T09:30:00",
        "funcionario": "Carla",
        "status": "cancelado"
    },
    {
        "cliente_email": "bruno.santos4@email.com",
        "servico": "corte",
        "dataHora": "2025-08-13T14:00:00",
        "funcionario": "Diana",
        "status": "confirmado"
    },
    {
        "cliente_email": "juliana.almeida5@email.com",
        "servico": "manicure",
        "dataHora": "2025-08-14T11:00:00",
        "funcionario": "Elisa",
        "status": "confirmado"
    },
    {
        "cliente_email": "ricardo.oliveira6@email.com",
        "servico": "hidratação",
        "dataHora": "2025-08-15T10:00:00",
        "funcionario": "Fábio",
        "status": "confirmado"
    },
    {
        "cliente_email": "patricia.costa7@email.com",
        "servico": "corte",
        "dataHora": "2025-08-16T13:00:00",
        "funcionario": "Ana",
        "status": "confirmado"
    },
    {
        "cliente_email": "thiago.martins8@email.com",
        "servico": "pintura de cabelo",
        "dataHora": "2025-08-17T15:00:00",
        "funcionario": "Bianca",
        "status": "confirmado"
    },
    {
        "cliente_email": "carla.nunes9@email.com",
        "servico": "manicure",
        "dataHora": "2025-08-18T09:00:00",
        "funcionario": "Carla",
        "status": "cancelado"
    },
    {
        "cliente_email": "diego.ribeiro10@email.com",
        "servico": "corte",
        "dataHora": "2025-08-19T11:00:00",
        "funcionario": "Diana",
        "status": "confirmado"
    },
    {
        "cliente_email": "isabela.moreira11@email.com",
        "servico": "manicure",
        "dataHora": "2025-08-20T14:30:00",
        "funcionario": "Elisa",
        "status": "confirmado"
    },
    {
        "cliente_email": "marcos.lima12@email.com",
        "servico": "escova",
        "dataHora": "2025-08-21T10:00:00",
        "funcionario": "Fábio",
        "status": "confirmado"
    },
    {
        "cliente_email": "natalia.santos13@email.com",
        "servico": "corte",
        "dataHora": "2025-08-22T15:00:00",
        "funcionario": "Ana",
        "status": "confirmado"
    },
    {
        "cliente_email": "paulo.almeida14@email.com",
        "servico": "pintura de cabelo",
        "dataHora": "2025-08-23T11:00:00",
        "funcionario": "Bianca",
        "status": "confirmado"
    },
    {
        "cliente_email": "renata.ferreira15@email.com",
        "servico": "hidratação",
        "dataHora": "2025-08-24T09:00:00",
        "funcionario": "Carla",
        "status": "confirmado"
    },
    {
        "cliente_email": "sandro.gomes16@email.com",
        "servico": "corte",
        "dataHora": "2025-08-25T13:30:00",
        "funcionario": "Diana",
        "status": "confirmado"
    },
    {
        "cliente_email": "tatiana.rocha17@email.com",
        "servico": "manicure",
        "dataHora": "2025-08-26T10:00:00",
        "funcionario": "Elisa",
        "status": "confirmado"
    },
    {
        "cliente_email": "vitor.carvalho18@email.com",
        "servico": "hidratação",
        "dataHora": "2025-08-27T14:00:00",
        "funcionario": "Fábio",
        "status": "confirmado"
    },
    {
        "cliente_email": "fernanda.lima1@email.com",
        "servico": "escova",
        "dataHora": "2025-08-28T09:00:00",
        "funcionario": "Ana",
        "status": "confirmado"
    },
    {
        "cliente_email": "lucas.souza2@email.com",
        "servico": "manicure",
        "dataHora": "2025-08-29T11:00:00",
        "funcionario": "Bianca",
        "status": "confirmado"
    }
]
db.servicos.insert_many(servicos_exemplos)
db.campanhas.insert_many(campanhas_exemplos)
db.feedbacks.insert_many(feedbacks_exemplos)
db.agendamentos.insert_many(agendamentos_exemplos)
db.clientes.insert_many(clientes_exemplos)


servicos_para_visitas = [
    "manicure", "escova", "hidratação", "pintura de cabelo", "corte", 
    "spa capilar", "massagem relaxante", "alongamento de unhas", "design de sobrancelhas"
]

for c in clientes_exemplos:
    # Verifica se o cliente já existe no banco
    cliente_existente = clientes.find_one({"email": c["email"]})
    
    if not cliente_existente:
        continue  # pula se o cliente não existir

    visitas = []
    data_base = datetime.strptime(c["ultimaVisita"], "%Y-%m-%d")

    for i in range(10):
        data_visita = (data_base - timedelta(days=3 * (9 - i))).strftime("%Y-%m-%d")
        servico = random.choice(servicos_para_visitas)
        visitas.append({"data": data_visita, "serviço": servico})

    # Adiciona as visitas ao array existente
    clientes.update_one(
        {"email": c["email"]},
        {
            "$push": {"visitas": {"$each": visitas}},
            "$set": {"ultimaVisita": visitas[-1]["data"]}
        }
    )
