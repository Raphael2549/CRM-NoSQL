from fastapi import FastAPI
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from typing import Optional
from datetime import datetime
from datetime import datetime, timedelta
import random
from contextlib import asynccontextmanager
from collections import Counter



uri = "mongodb+srv://raphaelbatista:@ufu-nosql.lu5rjbx.mongodb.net/?retryWrites=true&w=majority&appName=UFU-NoSQL"

client = MongoClient(uri, server_api=ServerApi('1'))
# Define banco e coleções
db = client["CRM_Salão"]
clientes = db["clientes"]
servicos = db["servicos"]
campanhas = db["campanhas"]
feedbacks = db["feedbacks"]
agendamentos = db["agendamentos"]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Criar índices na inicialização da API
    clientes.create_index("email", unique=True)
    campanhas.create_index("status")
    campanhas.create_index("segmento")
    feedbacks.create_index("servico")
    agendamentos.create_index("status")

    yield

app = FastAPI(lifespan=lifespan)



@app.get("/clientes/preferencias_dinamicas")
def calcular_preferencias_dinamicamente(email: str):
    pipeline = [
        {"$match": {"email": email}},
        {"$unwind": "$visitas"},
        {"$group": {
            "_id": "$visitas.serviço",
            "quantidade": {"$sum": 1}
        }},
        {"$sort": {"quantidade": -1}},
        {"$limit": 3}
        ]
    
    resultados = list(clientes.aggregate(pipeline))
    
    if not resultados:
        return {"erro": "Cliente não encontrado ou sem visitas registradas"}
    
    preferencias_ordenadas = [doc["_id"] for doc in resultados]

    return {
        "email": email,
        "preferencias_calculadas": preferencias_ordenadas
    }


@app.get("/servicos/mais_comprados")
async def listar_servicos_mais_comprados():
    pipeline = [
        {"$unwind": "$visitas"},
        {"$group": {
            "_id": "$visitas.serviço",
            "quantidade": {"$sum": 1}
        }},
        {"$sort": {"quantidade": -1}}
    ]

    resultados = list(clientes.aggregate(pipeline))
    
    mais_comprados = [(doc["_id"], doc["quantidade"]) for doc in resultados]
    
    return {"servicos_mais_comprados": mais_comprados}


@app.get("/campanhas/ativas")
async def campanhas_ativas_para_segmento(segmento: Optional[str] = None):
    filtro = {"status": "ativa"}
    if segmento:
        filtro["segmento"] = segmento
    resultados = list(campanhas.find(filtro, {"_id": 0}))
    return {"campanhas": resultados}


@app.get("/feedbacks/media")
async def calcular_nota_media(servico: str):
    pipeline = [
        {"$match": {"servico": servico}},
        {"$group": {
            "_id": "$servico",
            "media": {"$avg": "$nota"},
            "quantidade": {"$sum": 1}
        }}
    ]
    
    resultado = list(feedbacks.aggregate(pipeline))
    
    if not resultado:
        return {"servico": servico, "mensagem": "Nenhum feedback encontrado."}
    
    dados = resultado[0]
    
    return {
        "servico": servico,
        "quantidade_feedbacks": dados["quantidade"],
        "nota_media": round(dados["media"], 2)
    }


@app.get("/agendamentos/status")
async def buscar_agendamentos_por_status(status: str = "confirmado"):
    pipeline = [
        {"$match": {"status": status}},
        {"$project": {"_id": 0}}
    ]
    
    resultados = list(agendamentos.aggregate(pipeline))
    return {"agendamentos": resultados}