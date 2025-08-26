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
import redis
from dotenv import load_dotenv
import time
# Em main.py, no topo do arquivo

# Substitua sua linha de importação de 'models' por esta linha completa:
from models import Cliente, UpdateCliente, Servico, UpdateServico, Agendamento, Feedback, Campanha, UpdateCampanha

# ... (resto do seu código) ...
load_dotenv()
redis_uri = os.getenv("REDIS_URL")
# Conectar ao Redis Cloud
redis_client = redis.from_url(redis_uri, decode_responses=True)
    


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
# Contar Clientes Únicos por Mês (com Redis HLL)
# --------------------------
@app.get("/clientes/unicos")
def contar_clientes_unicos_hll(mes: Optional[str] = None):
    """
    Retorna o número APROXIMADO de clientes únicos do mês informado
    usando Redis HyperLogLog. Se nenhum mês for passado, usa o mês atual.
    Formato do mês: AAAA-MM
    """
    if not mes:
        mes = datetime.now().strftime("%Y-%m")

    hll_key = f"clientes_unicos:{mes}"
    total_unicos = redis_client.pfcount(hll_key)

    return {"mes": mes, "clientes_unicos_aproximado": total_unicos}



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
# Remover cliente
# --------------------------
@app.delete("/clientes/{id}")
def remover_cliente(id: str):
    # Primeiro, encontra o cliente para pegar o e-mail antes de apagar
    cliente_a_remover = clientes.find_one({"_id": ObjectId(id)})
    if not cliente_a_remover:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    cliente_email = cliente_a_remover.get("email")

    # --- AÇÃO EM CASCATA: Cancelar Agendamentos Futuros ---
    if cliente_email:
        # Encontra agendamentos "confirmados" para este cliente a partir de agora
        agendamentos_cancelados = agendamentos.update_many(
            {
                "cliente_email": cliente_email,
                "status": "confirmado",
                "data_hora": {"$gte": datetime.now()}
            },
            {"$set": {"status": "cancelado_cliente_excluido"}}
        )
        print(f"{agendamentos_cancelados.modified_count} agendamentos futuros foram cancelados.")
    # --- FIM DA AÇÃO EM CASCATA ---
    
    # Agora, apaga o cliente do banco de dados
    result = clientes.delete_one({"_id": ObjectId(id)})
    
    if result.deleted_count == 0:
        # Esta verificação é uma segurança extra, embora o find_one acima já verifique
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
    return {"mensagem": "Cliente removido e agendamentos futuros cancelados com sucesso."}
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
    start_time = time.time()
    cache_key = "ranking_clientes"
    if (cache := redis_client.get(cache_key)):
        elapsed = time.time() - start_time
        return {"ranking_clientes": eval(cache), "tempo_execucao": f"{elapsed:.6f} segundos"}

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
    redis_client.setex(cache_key, 120, str(resultados))

    elapsed = time.time() - start_time
    return {"ranking_clientes": resultados, "tempo_execucao": f"{elapsed:.6f} segundos"}

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
def atualizar_servico(id: str, dados_update: UpdateServico):
    # Converte os dados recebidos para um dicionário
    update_data = dados_update.model_dump(exclude_unset=True, by_alias=True)
    
    # --- AÇÃO EM CASCATA: Bloquear Alteração de Nome ---
    # Verifica se o campo "nome" está presente nos dados enviados para atualização
    if "nome" in update_data:
        raise HTTPException(
            status_code=400, # Bad Request
            detail="A alteração do nome de um serviço não é permitida. Para isso, inative o serviço atual e crie um novo."
        )
    # --- FIM DA AÇÃO EM CASCATA ---

    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum dado para atualizar foi fornecido.")
    
    result = servicos.update_one({"_id": ObjectId(id)}, {"$set": update_data})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
        
    return {"mensagem": "Serviço atualizado com sucesso"}


# --------------------------
# Remover serviço
# --------------------------
@app.delete("/servicos/{id}")
def remover_servico(id: str):
    # Primeiro, encontra o serviço para pegar o nome
    servico_a_remover = servicos.find_one({"_id": ObjectId(id)})
    if not servico_a_remover:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")

    nome_servico = servico_a_remover.get("nome")

    # --- AÇÃO EM CASCATA: Verificar Agendamentos Futuros ---
    if nome_servico:
        agendamento_futuro = agendamentos.find_one({
            "servico": nome_servico,
            "status": "confirmado",
            "data_hora": {"$gte": datetime.now()}
        })
        
        # Se encontrou um agendamento, bloqueia a exclusão
        if agendamento_futuro:
            raise HTTPException(
                status_code=409, # 409 Conflict
                detail="Este serviço não pode ser excluído pois possui agendamentos futuros."
            )
    # --- FIM DA AÇÃO EM CASCATA ---
    
    # Se passou pela verificação, pode apagar o serviço
    result = servicos.delete_one({"_id": ObjectId(id)})
    
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
    cache_key = "servicos_mais_comprados"
    if (cache := redis_client.get(cache_key)):
        return {"servicos_mais_comprados": eval(cache)}

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
    redis_client.setex(cache_key, 120, str(mais_comprados))
    return {"servicos_mais_comprados": mais_comprados}


# --------------------------
# Cadastrar feedback
# --------------------------
@app.post("/feedbacks", status_code=201)
def cadastrar_feedback(feedback: Feedback):
    feedback_dict = feedback.model_dump(by_alias=True)
    feedbacks.insert_one(feedback_dict)

    # --- AÇÃO EM CASCATA: Invalidação de Cache ---
    # Tenta apagar as chaves de cache que dependem das notas de feedback
    try:
        # O "*" é um curinga para apagar todas as variações (top_5, top_10, etc.)
        keys_to_delete = redis_client.keys("top_servicos_*")
        if keys_to_delete:
            redis_client.delete(*keys_to_delete)
            print("Cache de 'top_servicos' invalidado com sucesso.")
    except Exception as e:
        print(f"AVISO: Falha ao invalidar o cache de feedbacks no Redis: {e}")
    # --- FIM DA AÇÃO EM CASCATA ---
        
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
    cache_key = f"top_servicos_{limite}"
    if (cache := redis_client.get(cache_key)):
        return {"top_servicos": eval(cache)}

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
    redis_client.setex(cache_key, 120, str(resultados))
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
    cache_key = "retorno_campanhas"
    if (cache := redis_client.get(cache_key)):
        return {"retorno_campanhas": eval(cache)}

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
    redis_client.setex(cache_key, 120, str(resultados))
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
# --------------------------
# Alterar status
# --------------------------



# --------------------------
# Criar agendamento
# --------------------------
@app.post("/agendamentos")
def criar_agendamento(agendamento: dict):
    db.agendamentos.insert_one(agendamento)
    return {"mensagem": "Agendamento criado com sucesso"}



# --------------------------
# Alterar status (Versão Final e Completa)
# --------------------------
@app.put("/agendamentos/{id}/status")
def alterar_status_agendamento(id: str, status: str):
    agendamento = agendamentos.find_one({"_id": ObjectId(id)})
    if not agendamento:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    agendamentos.update_one(
        {"_id": ObjectId(id)}, 
        {"$set": {"status": status}}
    )

    if status.lower() in ["concluido", "concluído"]:
        cliente_email = agendamento.get("cliente_email")
        data_hora_do_banco = agendamento.get("dataHora")

        if cliente_email and data_hora_do_banco:
            if isinstance(data_hora_do_banco, str):
                data_hora_obj = datetime.fromisoformat(data_hora_do_banco)
            else:
                data_hora_obj = data_hora_do_banco
            
            data_visita_str = data_hora_obj.strftime("%Y-%m-%d")

            nova_visita = {
                "data": data_visita_str,
                "serviço": agendamento.get("servico")
            }
            
            # --- LÓGICA ATUALIZADA ---
            # Adiciona a nova visita E atualiza o campo ultimaVisita
            clientes.update_one(
                {"email": cliente_email},
                {
                    "$addToSet": {"visitas": nova_visita},
                    "$set": {"ultimaVisita": data_visita_str}
                }
            )
            # --- FIM DA ATUALIZAÇÃO ---

            try:
                mes = data_hora_obj.strftime("%Y-%m")
                hll_key = f"clientes_unicos:{mes}"
                redis_client.pfadd(hll_key, cliente_email)
            except Exception as e:
                print(f"AVISO: Falha ao atualizar o HyperLogLog no Redis: {e}")

    return {"mensagem": f"Status do agendamento atualizado para '{status}' com sucesso."}