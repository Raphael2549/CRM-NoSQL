import os
import random
import time
import json
import certifi

from neo4j import GraphDatabase
from graphdatascience import GraphDataScience
from collections import Counter
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional

from bson import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import redis
# Importa todos os modelos Pydantic do arquivo models.py
from models import Cliente, UpdateCliente, Servico, UpdateServico, Agendamento, Feedback, Campanha, UpdateCampanha

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

# --- Configuração e Conexão com Neo4j GDS ---
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Tenta conectar ao GDS. Se falhar, a funcionalidade de análise fica desativada.
if not NEO4J_PASSWORD:
    print("AVISO: Senha do Neo4j (NEO4J_PASSWORD) não definida no .env. A análise de grafos será desativada.")
    gds = None
else:
    try:
        gds = GraphDataScience(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        gds.set_database("neo4j") # Garante que estamos usando o banco de dados padrão
        print("Conexão com a biblioteca Neo4j GDS bem-sucedida!")
    except Exception as e:
        print(f"AVISO: Não foi possível conectar ao GDS. A análise de grafos será desativada. Detalhe: {e}")
        gds = None

app = FastAPI()

# --------------------------
# Contagem EXATA de Clientes Únicos por Mês (via MongoDB com Cache)
# --------------------------
@app.get("/clientes/unicos")
def contar_clientes_unicos(mes: str):
    """
    Retorna o número EXATO de clientes únicos com visitas no mês informado.
    Formato do mês: AAAA-MM
    """
    cache_key = f"clientes_unicos_exatos:{mes}"
    if (cache := redis_client.get(cache_key)):
        return {"mes": mes, "clientes_unicos_exato": json.loads(cache), "fonte": "cache"}

    pipeline = [
        {"$unwind": "$visitas"},
        {"$match": {"visitas.data": {"$regex": f"^{mes}"}}},
        {"$group": {"_id": "$email"}},
        {"$count": "total_unicos"}
    ]
    
    resultado = list(clientes.aggregate(pipeline))
    total_unicos = resultado[0]['total_unicos'] if resultado else 0

    redis_client.setex(cache_key, 3600, json.dumps(total_unicos))

    return {"mes": mes, "clientes_unicos_exato": total_unicos, "fonte": "banco de dados"}

# --------------------------
#CADASTRO DE CLIENTES
# --------------------------
@app.post("/cadastro_clientes", status_code=201)
def cadastrar_cliente(cliente: Cliente):
    if clientes.find_one({"email": cliente.email}):
        raise HTTPException(status_code=409, detail="Cliente com este e-mail já cadastrado")
    
    cliente_dict = cliente.model_dump(by_alias=True)
    clientes.insert_one(cliente_dict)
    return {"mensagem": "Cliente cadastrado com sucesso", "cliente": cliente_dict}

# --------------------------
# Atualizar dados do cliente
# --------------------------
@app.put("/clientes/{id}")
def atualizar_cliente(id: str, dados_update: UpdateCliente):
    update_data = dados_update.model_dump(exclude_unset=True, by_alias=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum dado para atualizar foi fornecido.")

    result = clientes.update_one({"_id": ObjectId(id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return {"mensagem": "Cliente atualizado com sucesso"}

# --------------------------
# Remover cliente
# --------------------------
@app.delete("/clientes/{id}")
def remover_cliente(id: str):
    cliente_a_remover = clientes.find_one({"_id": ObjectId(id)})
    if not cliente_a_remover:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    cliente_email = cliente_a_remover.get("email")

    if cliente_email:
        agendamentos.update_many(
            {"cliente_email": cliente_email, "status": "confirmado", "data_hora": {"$gte": datetime.now()}},
            {"$set": {"status": "cancelado_cliente_excluido"}}
        )
    
    result = clientes.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
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

    pipeline.append({"$project": {"_id": 0}}) 

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
        {"$addFields": {"mesNascimento": {"$toInt": {"$substr": ["$dataNascimento", 5, 2]}}}},
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
        return {"ranking_clientes": json.loads(cache), "tempo_execucao": f"{elapsed:.6f} segundos"}

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
    redis_client.setex(cache_key, 120, json.dumps(resultados, default=str))

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
    return {"email": email, "preferencias_calculadas": preferencias_ordenadas}

# --------------------------
# Cadastrar serviço
# --------------------------
@app.post("/servicos", status_code=201)
def cadastrar_servico(servico: Servico):
    if servicos.find_one({"nome": servico.nome}):
        raise HTTPException(status_code=409, detail="Serviço com este nome já cadastrado")
    servico_dict = servico.model_dump(by_alias=True)
    servicos.insert_one(servico_dict)
    return {"mensagem": "Serviço cadastrado com sucesso", "servico": servico_dict}

# --------------------------
# Atualizar serviço
# --------------------------
@app.put("/servicos/{id}")
def atualizar_servico(id: str, dados_update: UpdateServico):
    update_data = dados_update.model_dump(exclude_unset=True, by_alias=True)
    
    if "nome" in update_data:
        raise HTTPException(
            status_code=400,
            detail="A alteração do nome de um serviço não é permitida. Para isso, inative o serviço atual e crie um novo."
        )

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
    servico_a_remover = servicos.find_one({"_id": ObjectId(id)})
    if not servico_a_remover:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")

    nome_servico = servico_a_remover.get("nome")

    if nome_servico:
        agendamento_futuro = agendamentos.find_one({
            "servico": nome_servico,
            "status": "confirmado",
            "data_hora": {"$gte": datetime.now()}
        })
        
        if agendamento_futuro:
            raise HTTPException(
                status_code=409,
                detail="Este serviço não pode ser excluído pois possui agendamentos futuros."
            )
    
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
        {"$group": {
            "_id": "$categoria",
            "servicos": {"$push": {"nome": "$nome", "preco": "$preco", "duracaoMinutos": "$duracaoMinutos"}},
            "total_servicos": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    resultados = list(servicos.aggregate(pipeline))
    return {"categorias": resultados}

# --------------------------
# Ranking de serviços mais comprados
# --------------------------
@app.get("/servicos/mais_comprados")
def listar_servicos_mais_comprados():
    cache_key = "servicos_mais_comprados"
    if (cache := redis_client.get(cache_key)):
        return {"servicos_mais_comprados": json.loads(cache)}

    pipeline = [
        {"$unwind": "$visitas"},
        {"$group": {"_id": "$visitas.serviço", "quantidade": {"$sum": 1}}},
        {"$sort": {"quantidade": -1}}
    ]
    resultados = list(clientes.aggregate(pipeline))
    redis_client.setex(cache_key, 120, json.dumps(resultados, default=str))
    return {"servicos_mais_comprados": resultados}

# --------------------------
# Cadastrar feedback
# --------------------------
@app.post("/feedbacks", status_code=201)
def cadastrar_feedback(feedback: Feedback):
    feedback_dict = feedback.model_dump(by_alias=True)
    feedbacks.insert_one(feedback_dict)

    try:
        keys_to_delete = redis_client.keys("top_servicos_*")
        if keys_to_delete:
            redis_client.delete(*keys_to_delete)
    except Exception as e:
        print(f"AVISO: Falha ao invalidar o cache de feedbacks no Redis: {e}")
        
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
        return {"top_servicos": json.loads(cache)}

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
    redis_client.setex(cache_key, 120, json.dumps(resultados, default=str))
    return {"top_servicos": resultados}

# --------------------------
# Avaliação média dos feedbacks de todos os serviços
# --------------------------
@app.get("/feedbacks/media")
def calcular_nota_media(servico: str):
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
@app.post("/campanhas", status_code=201)
def criar_campanha(campanha: Campanha):
    campanha_dict = campanha.model_dump(by_alias=True)
    campanhas.insert_one(campanha_dict)
    return {"mensagem": "Campanha criada com sucesso"}

# --------------------------
# 2. Atualizar campanha
# --------------------------
@app.put("/campanhas/{id}")
def atualizar_campanha(id: str, dados_update: UpdateCampanha):
    update_data = dados_update.model_dump(exclude_unset=True, by_alias=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum dado para atualizar foi fornecido.")
    
    result = campanhas.update_one({"_id": ObjectId(id)}, {"$set": update_data})
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
        return {"retorno_campanhas": json.loads(cache)}

    pipeline = [
        {"$lookup": {
            "from": "clientes",
            "localField": "segmento",
            "foreignField": "segmento",
            "as": "clientes_segmento"
        }},
        {"$lookup": {
            "from": "agendamentos",
            "localField": "nome",
            "foreignField": "campanha_nome",
            "as": "agendamentos_campanha"
        }},
        {"$project": {
            "_id": 0,
            "nome": 1,
            "clientes_impactados": {"$size": "$clientes_segmento"},
            "agendamentos_realizados": {"$size": "$agendamentos_campanha"}
        }}
    ]
    resultados = list(campanhas.aggregate(pipeline))
    redis_client.setex(cache_key, 120, json.dumps(resultados, default=str))
    return {"retorno_campanhas": resultados}

# --------------------------
# Listar campanhas ativas
# --------------------------
@app.get("/campanhas/ativas")
def campanhas_ativas_para_segmento(segmento: Optional[str] = None):
    filtro = {"status": "ativa"}
    if segmento:
        filtro["segmento"] = segmento
    resultados = list(campanhas.find(filtro, {"_id": 0}))
    return {"campanhas": resultados}


# --------------------------
# Meta Diária de Clientes
# --------------------------
@app.get("/campanhas/meta-diaria")
def get_daily_goal_status(data: Optional[str] = None):
    """
    Verifica o status da campanha "primeiros 5 clientes do dia".
    Se nenhuma data for fornecida, usa a data atual.
    Formato da data: AAAA-MM-DD
    """
    # Se nenhuma data for passada, usa a data de hoje como padrão
    if data is None:
        data = datetime.now().strftime("%Y-%m-%d")
    
    meta_do_dia = 5
    chave_meta = f"meta_diaria:{data}"
    
    # Conta quantos clientes únicos foram atendidos na data especificada
    clientes_atendidos = redis_client.bitcount(chave_meta)
    
    clientes_restantes = meta_do_dia - clientes_atendidos
    
    if clientes_restantes < 0:
        clientes_restantes = 0
        
    campanha_ainda_valida = clientes_atendidos < meta_do_dia
        
    return {
        "data": data,
        "meta_clientes_unicos": meta_do_dia,
        "clientes_atingidos_hoje": clientes_atendidos, # Mudei o nome para ser mais genérico
        "clientes_restantes_para_meta": clientes_restantes,
        "campanha_ainda_valida": campanha_ainda_valida
    }

# --------------------------
# Criar agendamento
# --------------------------
@app.post("/agendamentos", status_code=201)
def criar_agendamento(agendamento: Agendamento):
    cliente_existente = clientes.find_one({"email": agendamento.cliente_email})
    if not cliente_existente:
        raise HTTPException(
            status_code=404, 
            detail="Cliente não encontrado. Não é possível criar um agendamento para um cliente não cadastrado."
        )
    
    agendamento_dict = agendamento.model_dump(by_alias=True)
    
    # --- INÍCIO DA CORREÇÃO ---
    # Insere o documento e pega o resultado da inserção
    resultado_insert = agendamentos.insert_one(agendamento_dict)
    # Busca o documento recém-criado usando o ID retornado
    agendamento_criado = agendamentos.find_one({"_id": resultado_insert.inserted_id})
    # Converte o campo _id para string
    agendamento_criado["_id"] = str(agendamento_criado["_id"])
    # --- FIM DA CORREÇÃO ---
    
    return {"mensagem": "Agendamento criado com sucesso", "agendamento": agendamento_criado}

# --------------------------
# Alterar status (Com lógica de meta limitada a 5)
# --------------------------
# Em main.py

# Em main.py

# Em main.py

# --------------------------
# Alterar status (Versão com a correção final do nome do campo)
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

    mensagem_retorno = {"mensagem": f"Status do agendamento atualizado para '{status}' com sucesso."}

    if status.lower() in ["concluido", "concluído"]:
        # --- INÍCIO DA CORREÇÃO ---
        # Corrigido de "cliente_email" para "clienteEmail" para corresponder ao que está no banco
        cliente_email = agendamento.get("clienteEmail")
        data_hora_do_banco = agendamento.get("dataHora")
        # --- FIM DA CORREÇÃO ---

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
            
            clientes.update_one(
                {"email": cliente_email},
                {
                    "$addToSet": {"visitas": nova_visita},
                    "$set": {"ultimaVisita": data_visita_str}
                }
            )

            try:
                mes = data_hora_obj.strftime("%Y-%m")
                redis_client.delete(f"clientes_unicos_exatos:{mes}")
                redis_client.delete("ranking_clientes")
                redis_client.delete("servicos_mais_comprados")

                meta_do_dia = 5
                chave_meta = f"meta_diaria:{data_hora_obj.strftime('%Y-%m-%d')}"
                chave_mapeamento = "email_para_id"
                
                id_cliente = redis_client.hget(chave_mapeamento, cliente_email)
                if id_cliente is None:
                    id_cliente = redis_client.incr("proximo_id_cliente")
                    redis_client.hset(chave_mapeamento, cliente_email, id_cliente)
                id_cliente = int(id_cliente)

                ja_veio_hoje = redis_client.getbit(chave_meta, id_cliente)

                if ja_veio_hoje == 0:
                    contagem_atual = redis_client.bitcount(chave_meta)
                    if contagem_atual < meta_do_dia:
                        redis_client.setbit(chave_meta, id_cliente, 1)
                        mensagem_retorno["promocao_diaria"] = f"Parabéns! Este foi o cliente único número {contagem_atual + 1} de {meta_do_dia}."
                    else:
                        mensagem_retorno["promocao_diaria"] = f"Meta de {meta_do_dia} clientes únicos já atingida para o dia {data_hora_obj.strftime('%Y-%m-%d')}."
                else:
                    mensagem_retorno["promocao_diaria"] = "Cliente já foi contado para a meta deste dia."

            except Exception as e:
                print(f"AVISO: Falha na comunicação com o Redis: {e}")

    return mensagem_retorno
# --------------------------
# Taxa de ocupação por dia/semana/mês
# --------------------------
@app.get("/agendamentos/ocupacao")
def taxa_ocupacao(periodo: str = "dia"):
    if periodo not in ["dia", "semana", "mes"]:
        raise HTTPException(status_code=400, detail="Período inválido. Use: dia, semana ou mes.")

    cache_key = f"ocupacao_{periodo}"
    if (cache := redis_client.get(cache_key)):
        return {"ocupacao_por_" + periodo: json.loads(cache)}

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
    resultados = list(agendamentos.aggregate(pipeline))
    redis_client.setex(cache_key, 120, json.dumps(resultados, default=str))
    return {"ocupacao_por_" + periodo: resultados}

@app.get("/clientes/similares/{email_cliente}", tags=["Análise de Grafos (GDS)"])
def encontrar_clientes_similares(email_cliente: str, top_k: int = 5):
    """
    Encontra os 'top_k' clientes mais similares a um cliente específico,
    baseado nos serviços que eles compraram em comum (Índice de Jaccard).
    Funciona na Edição Community do Neo4j.
    """
    if gds is None:
        raise HTTPException(status_code=503, detail="Serviço de Análise de Grafos (GDS) indisponível.")

    graph_name = "crm-similarity-graph"

    try:

        if gds.graph.exists(graph_name).exists:
            gds.run_cypher(f"CALL gds.graph.drop('{graph_name}', false)")

        gds.run_cypher(f"""
            CALL gds.graph.project(
                '{graph_name}',
                ['Cliente', 'Servico'],
                {{
                    COMPROU: {{ orientation: 'UNDIRECTED' }}
                }}
            )
        """)

        cypher_query = f"""
            CALL gds.nodeSimilarity.stream('{graph_name}')
            YIELD node1, node2, similarity
            WITH gds.util.asNode(node1) AS cliente1, gds.util.asNode(node2) AS cliente2, similarity
            WHERE cliente1.email = $email_cliente AND cliente1 <> cliente2
            RETURN
                cliente2.nome AS nome,
                cliente2.email AS email,
                similarity
            ORDER BY similarity DESC
            LIMIT $top_k
        """
        
        results = gds.run_cypher(
            cypher_query,
            params={
                "email_cliente": email_cliente,
                "top_k": top_k
            }
        )

        if results.empty:
            return {
                "cliente_origem": email_cliente,
                "clientes_similares": []
            }

        return {
            "cliente_origem": email_cliente,
            "clientes_similares": results.to_dict('records')
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro durante a análise de grafos: {e}")

    finally:---
        if gds and gds.graph.exists(graph_name).exists:
            gds.run_cypher(f"CALL gds.graph.drop('{graph_name}', false)")