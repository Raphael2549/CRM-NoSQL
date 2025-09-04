import os
import certifi
from pymongo import MongoClient
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env para o ambiente
load_dotenv()

# --- Configurações das Conexões ---
MONGO_URI = os.getenv("MONGODB_URI")
MONGO_DB_NAME = "CRM_Salão"
NEO4J_URI = "neo4j://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_PASSWORD:
    raise ValueError("A senha do Neo4j (NEO4J_PASSWORD) não foi encontrada no arquivo .env")

# --- Conexão com os Bancos e Definição das Coleções ---
try:
    # Conexão com o MongoDB
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client[MONGO_DB_NAME]

    # Define as coleções, igual no seu app principal
    clientes_collection = db.clientes
    servicos_collection = db.servicos
    feedbacks_collection = db.feedbacks # Se for usar para migrar feedbacks também

    # Conexão com o Neo4j
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    neo4j_driver.verify_connectivity()
    print("Conexão com MongoDB e Neo4j bem-sucedida!")
except Exception as e:
    print(f"ERRO: Falha ao conectar com os bancos de dados: {e}")
    exit()

def carregar_clientes(session):
    print("Carregando clientes...")
    # Usa a variável da coleção definida no início do script
    for cliente in clientes_collection.find():
        session.run("""
            MERGE (c:Cliente {email: $email})
            SET c.nome = $nome, c.dataNascimento = $dataNascimento
        """, email=cliente.get("email"), nome=cliente.get("nome"), dataNascimento=cliente.get("dataNascimento"))
    print("-> Clientes carregados.")

def carregar_servicos(session):
    print("Carregando serviços...")
    # Usa a variável da coleção definida no início do script
    for servico in servicos_collection.find():
        session.run("""
            MERGE (s:Servico {nome: $nome})
            SET s.preco = $preco, s.categoria = $categoria, s.duracaoMinutos = $duracao
        """, nome=servico.get("nome"), preco=servico.get("preco"), categoria=servico.get("categoria"), duracao=servico.get("duracaoMinutos"))
    print("-> Serviços carregados.")

def carregar_relacionamentos_compra(session):
    print("Carregando relacionamentos de compra (visitas)...")
    # Usa a variável da coleção definida no início do script
    for cliente in clientes_collection.find({"visitas": {"$exists": True, "$ne": []}}):
        for visita in cliente.get("visitas", []):
            session.run("""
                MATCH (c:Cliente {email: $email})
                MATCH (s:Servico {nome: $servico})
                MERGE (c)-[r:COMPROU {data: $data}]->(s)
            """, email=cliente.get("email"), servico=visita.get("serviço"), data=visita.get("data"))
    print("-> Relacionamentos de compra carregados.")

def run_migration():
    with neo4j_driver.session() as session:
        print("Garantindo a existência de constraints no Neo4j...")
        session.run("CREATE CONSTRAINT cliente_email_unique IF NOT EXISTS FOR (c:Cliente) REQUIRE c.email IS UNIQUE;")
        session.run("CREATE CONSTRAINT servico_nome_unique IF NOT EXISTS FOR (s:Servico) REQUIRE s.nome IS UNIQUE;")
        print("-> Constraints verificadas.")
        
        carregar_clientes(session)
        carregar_servicos(session)
        carregar_relacionamentos_compra(session)

if __name__ == "__main__":
    try:
        run_migration()
    finally:
        mongo_client.close()
        neo4j_driver.close()
        print("\nProcesso de migração finalizado.")