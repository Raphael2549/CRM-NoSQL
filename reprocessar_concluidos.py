# reprocessar_concluidos.py (agora atualizando a ultimaVisita)
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import redis
import os
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv("MONGODB_URI")
client = MongoClient(mongo_uri, server_api=ServerApi('1'))
db = client["CRM_Salão"]
agendamentos_collection = db["agendamentos"]
clientes_collection = db["clientes"]

redis_uri = os.getenv("REDIS_URL")
redis_client = redis.from_url(redis_uri, decode_responses=True)

print("Iniciando o reprocessamento para adicionar visitas e atualizar a ultimaVisita...")

query = {"status": {"$regex": "^Concluído$", "$options": "i"}}
agendamentos_concluidos = agendamentos_collection.find(query)

registros_processados = 0
for agendamento in agendamentos_concluidos:
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
        # Adiciona a nova visita E atualiza o campo ultimaVisita em uma única operação
        clientes_collection.update_one(
            {"email": cliente_email},
            {
                "$addToSet": {"visitas": nova_visita},
                "$set": {"ultimaVisita": data_visita_str}
            }
        )
        # --- FIM DA ATUALIZAÇÃO ---

        mes = data_hora_obj.strftime("%Y-%m")
        hll_key = f"clientes_unicos:{mes}"
        redis_client.pfadd(hll_key, cliente_email)
        
        registros_processados += 1

print(f"Reprocessamento concluído! {registros_processados} agendamentos foram sincronizados.")