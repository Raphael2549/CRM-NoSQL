from fastapi import FastAPI, HTTPException
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from typing import Optional
from datetime import datetime
from datetime import datetime, timedelta
import random
from contextlib import asynccontextmanager
from collections import Counter
import os
from bson import ObjectId


mongo_uri = os.getenv("MONGODB_URI")


client = MongoClient(mongo_uri, server_api=ServerApi('1'))
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
# --------------------------
#CADASTRO DE CLIENTES
# --------------------------
@app.post("/cadastro_clientes")
def cadastrar_cliente(cliente: dict):
    if clientes.find_one({"email": cliente.get("email")}):
        raise HTTPException(status_code=400, detail="Cliente já cadastrado")
    clientes.insert_one(cliente)
    return {"mensagem": "Cliente cadastrado com sucesso"}

# --------------------------
# Atualizar dados do cliente
# --------------------------
@app.put("/clientes/{id}")
def atualizar_cliente(id: str, dados: dict):
    result = clientes.update_one({"_id": ObjectId(id)}, {"$set": dados})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return {"mensagem": "Cliente atualizado com sucesso"}

# --------------------------
# Listar todos ou buscar por filtros
# --------------------------
@app.get("/clientes")
def listar_clientes(nome: Optional[str] = None, email: Optional[str] = None, ultima_visita: Optional[str] = None):
    pipeline = []

    match_stage = {}
    if nome:
        match_stage["nome"] = {"$regex": nome, "$options": "i"}
    if email:
        match_stage["email"] =  email
    if ultima_visita:
        match_stage["ultimaVisita"] = ultima_visita

    if match_stage:
        pipeline.append({"$match": match_stage})

    pipeline.append({"$project": {"_id": 0}})  # remove _id para retorno mais limpo

    resultados = list(clientes.aggregate(pipeline))
    return {"clientes": resultados}

# --------------------------
# Aniversariantes do mês
# --------------------------
@app.get("/clientes/aniversariantes")
def aniversariantes_do_mes(mes: Optional[int] = None):
    if mes is None:
        mes = datetime.now().month

    pipeline = [
        {
            "$addFields": {
                "mesNascimento": {"$toInt": {"$substr": ["$dataNascimento", 5, 2]}}
            }
        },
        {"$match": {"mesNascimento": mes}},
        {"$project": {"_id": 0, "nome": 1, "email": 1, "dataNascimento": 1}}
    ]

    resultados = list(clientes.aggregate(pipeline))
    return {"mes": mes, "aniversariantes": resultados}

# --------------------------
# Ranking de clientes mais frequentes
# --------------------------
@app.get("/clientes/frequencia")
def ranking_clientes_frequentes():
    pipeline = [
        {"$unwind": "$visitas"},
        {"$group": {
            "_id": "$email",
            "nome": {"$first": "$nome"},
            "quantidade_visitas": {"$sum": 1},
            "valor_total_gasto": {"$first": "$valorGastoTotal"}
        }},
        {"$sort": {"quantidade_visitas": -1}}
    ]

    resultados = list(clientes.aggregate(pipeline))
    return {"ranking_clientes": resultados}

# --------------------------
# Encontrar preferências de um cliente específico
# --------------------------
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


# --------------------------
# Cadastrar serviço
# --------------------------
@app.post("/servicos")
def cadastrar_servico(servico: dict):
    if db.servicos.find_one({"nome": servico.get("nome")}):
        raise HTTPException(status_code=400, detail="Serviço já cadastrado")
    db.servicos.insert_one(servico)
    return {"mensagem": "Serviço cadastrado com sucesso"}

# --------------------------
# Atualizar serviço
# --------------------------
@app.put("/servicos/{id}")
def atualizar_servico(id: str, dados: dict):
    result = db.servicos.update_one({"_id": ObjectId(id)}, {"$set": dados})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    return {"mensagem": "Serviço atualizado com sucesso"}

# --------------------------
# Remover serviço
# --------------------------
@app.delete("/servicos/{id}")
def remover_servico(id: str):
    result = db.servicos.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    return {"mensagem": "Serviço removido com sucesso"}

# --------------------------
# Agrupar serviços por categoria 
# --------------------------
@app.get("/servicos/categorias")
def listar_servicos_por_categoria():
    pipeline = [
        {
            "$group": {
                "_id": "$categoria",
                "servicos": {"$push": {"nome": "$nome", "preco": "$preco", "duracaoMinutos": "$duracaoMinutos"}},
                "total_servicos": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    resultados = list(db.servicos.aggregate(pipeline))
    return {"categorias": resultados}

# --------------------------
# Ranking de serviços mais comprados
# --------------------------
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



# --------------------------
# Cadastrar feedback
# --------------------------
@app.post("/feedbacks")
def cadastrar_feedback(feedback: dict):
    feedback["data"] = feedback.get("data", datetime.now().strftime("%Y-%m-%d"))
    feedbacks.insert_one(feedback)
    return {"mensagem": "Feedback cadastrado com sucesso"}

# --------------------------
# Últimos feedbacks recebidos
# --------------------------
@app.get("/feedbacks/ultimos")
def ultimos_feedbacks(limite: int = 10):
    pipeline = [
        {"$sort": {"data": -1}},
        {"$limit": limite},
        {"$project": {"_id": 0}}
    ]
    resultados = list(feedbacks.aggregate(pipeline))
    return {"ultimos_feedbacks": resultados}

# --------------------------
# Listar notas abaixo de 4
# --------------------------
@app.get("/feedbacks/negativos")
def feedbacks_negativos(limite: int = 10, nota_maxima: int = 4):
    pipeline = [
        {"$match": {"nota": {"$lte": nota_maxima}}},
        {"$sort": {"data": -1}},
        {"$limit": limite},
        {"$project": {"_id": 0}}
    ]
    resultados = list(feedbacks.aggregate(pipeline))
    return {"feedbacks_negativos": resultados}

# --------------------------
# Top serviços com melhor avaliação média
# --------------------------
@app.get("/feedbacks/top")
def top_servicos_mais_bem_avaliados(limite: int = 5):
    pipeline = [
        {"$group": {
            "_id": "$servico",
            "media_nota": {"$avg": "$nota"},
            "qtd_feedbacks": {"$sum": 1}
        }},
        {"$sort": {"media_nota": -1}},
        {"$limit": limite}
    ]
    resultados = list(feedbacks.aggregate(pipeline))
    return {"top_servicos": resultados}

# --------------------------
# Avaliação média dos feedbacks de todos os serviços
# --------------------------
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


# --------------------------
# Criar campanha
# --------------------------

@app.post("/campanhas")
def criar_campanha(campanha: dict):
    campanhas.insert_one(campanha)
    return {"mensagem": "Campanha criada com sucesso"}

# --------------------------
# 2. Atualizar campanha
# --------------------------
@app.put("/campanhas/{id}")
def atualizar_campanha(id: str, dados: dict):
    result = campanhas.update_one({"_id": ObjectId(id)}, {"$set": dados})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    return {"mensagem": "Campanha atualizada com sucesso"}

# --------------------------
# Segmentar clientes para campanhas personalizadas
# --------------------------
@app.get("/campanhas/por-segmento")
def campanhas_por_segmento(segmento: str):
    pipeline = [
        {"$match": {"segmento": segmento}},
        {"$project": {"_id": 0}}
    ]
    resultados = list(campanhas.aggregate(pipeline))
    return {"campanhas": resultados}

# --------------------------
# Medir retorno de campanhas
# --------------------------
@app.get("/campanhas/retorno")
def retorno_campanhas():
    # Exemplo: para cada campanha, conta quantos clientes do segmento participaram e quantos agendaram serviço
    pipeline = [
        {
            "$lookup": {
                "from": "clientes",
                "localField": "segmento",
                "foreignField": "segmento",
                "as": "clientes_segmento"
            }
        },
        {
            "$lookup": {
                "from": "agendamentos",
                "localField": "nome",
                "foreignField": "campanha_nome",
                "as": "agendamentos_campanha"
            }
        },
        {
            "$project": {
                "_id": 0,
                "nome": 1,
                "clientes_impactados": {"$size": "$clientes_segmento"},
                "agendamentos_realizados": {"$size": "$agendamentos_campanha"}
            }
        }
    ]
    resultados = list(campanhas.aggregate(pipeline))
    return {"retorno_campanhas": resultados}

# --------------------------
# Listar campanhas ativas
# --------------------------
@app.get("/campanhas/ativas")
async def campanhas_ativas_para_segmento(segmento: Optional[str] = None):
    filtro = {"status": "ativa"}
    if segmento:
        filtro["segmento"] = segmento
    resultados = list(campanhas.find(filtro, {"_id": 0}))
    return {"campanhas": resultados}


# --------------------------
# Busca de agendamento por status
# --------------------------
@app.get("/agendamentos/status")
async def buscar_agendamentos_por_status(status: str = "confirmado"):
    pipeline = [
        {"$match": {"status": status}},
        {"$project": {"_id": 0}}
    ]
    
    resultados = list(agendamentos.aggregate(pipeline))
    return {"agendamentos": resultados}

# --------------------------
# Criar agendamento
# --------------------------
@app.post("/agendamentos")
def criar_agendamento(agendamento: dict):
    db.agendamentos.insert_one(agendamento)
    return {"mensagem": "Agendamento criado com sucesso"}

# --------------------------
# Alterar status
# --------------------------
@app.put("/agendamentos/{id}/status")
def alterar_status_agendamento(id: str, status: str):
    result = db.agendamentos.update_one({"_id": ObjectId(id)}, {"$set": {"status": status}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    return {"mensagem": "Status atualizado com sucesso"}

# --------------------------
# Agendamentos de um dia específico
# --------------------------
@app.get("/agendamentos/por-data")
def listar_agendamentos_por_data(data: str):
    pipeline = [
        {"$match": {"dataHora": {"$regex": f"^{data}"}}},
        {"$project": {"_id": 0}}
    ]
    resultados = list(db.agendamentos.aggregate(pipeline))
    return {"data": data, "agendamentos": resultados}

# --------------------------
# Taxa de ocupação por dia/semana/mês
# --------------------------
@app.get("/agendamentos/ocupacao")
def taxa_ocupacao(periodo: str = "dia"):
    if periodo not in ["dia", "semana", "mes"]:
        raise HTTPException(status_code=400, detail="Período inválido. Use: dia, semana ou mes.")

    formatos = {
        "dia": {"$dateToString": {"format": "%Y-%m-%d", "date": {"$toDate": "$dataHora"}}},
        "semana": {"$dateToString": {"format": "%Y-%U", "date": {"$toDate": "$dataHora"}}},
        "mes": {"$dateToString": {"format": "%Y-%m", "date": {"$toDate": "$dataHora"}}}
    }

    pipeline = [
        {"$addFields": {"periodo": formatos[periodo]}},
        {"$group": {
            "_id": "$periodo",
            "total_agendamentos": {"$sum": 1},
            "confirmados": {"$sum": {"$cond": [{"$eq": ["$status", "confirmado"]}, 1, 0]}},
            "cancelados": {"$sum": {"$cond": [{"$eq": ["$status", "cancelado"]}, 1, 0]}}
        }},
        {"$sort": {"_id": 1}}
    ]

    resultados = list(db.agendamentos.aggregate(pipeline))
    return {"ocupacao_por_" + periodo: resultados}