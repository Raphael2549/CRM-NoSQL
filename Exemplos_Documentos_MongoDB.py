from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://raphaelbatista:@ufu-nosql.lu5rjbx.mongodb.net/?retryWrites=true&w=majority&appName=UFU-NoSQL"

client = MongoClient(uri, server_api=ServerApi('1'))

db = client["CRM_Salão"]

clientes = db["clientes"]

clientes_exemplos = [
    {
        "nome": "Maria Oliveira",
        "email": "maria.oliveira@email.com",
        "telefone": "11999999999",
        "dataNascimento": "1985-05-20",
        "preferencias": ["corte", "hidratação", "manicure"],
        "visitas": [
            {"data": "2025-07-10", "serviço": "corte"},
            {"data": "2025-06-05", "serviço": "hidratação"}
        ],
        "ultimaVisita": "2025-07-10",
        "valorGastoTotal": 850.00
    },
    {
        "nome": "Ana Silva",
        "email": "ana.silva@email.com",
        "telefone": "11988888888",
        "dataNascimento": "1990-03-15",
        "preferencias": ["manicure", "pintura de cabelo"],
        "visitas": [
            {"data": "2025-07-12", "serviço": "manicure"},
            {"data": "2025-06-20", "serviço": "pintura de cabelo"}
        ],
        "ultimaVisita": "2025-07-12",
        "valorGastoTotal": 600.00
    },
    {
        "nome": "Carla Mendes",
        "email": "carla.mendes@email.com",
        "telefone": "11977777777",
        "dataNascimento": "1988-08-22",
        "preferencias": ["hidratação", "escova"],
        "visitas": [
            {"data": "2025-07-08", "serviço": "hidratação"},
            {"data": "2025-05-30", "serviço": "escova"}
        ],
        "ultimaVisita": "2025-07-08",
        "valorGastoTotal": 730.00
    },
    {
        "nome": "Juliana Costa",
        "email": "juliana.costa@email.com",
        "telefone": "11966666666",
        "dataNascimento": "1992-12-01",
        "preferencias": ["corte", "manicure", "escova"],
        "visitas": [
            {"data": "2025-07-05", "serviço": "corte"},
            {"data": "2025-06-15", "serviço": "manicure"}
        ],
        "ultimaVisita": "2025-07-05",
        "valorGastoTotal": 490.00
    },
    {
        "nome": "Patrícia Gomes",
        "email": "patricia.gomes@email.com",
        "telefone": "11955555555",
        "dataNascimento": "1983-11-10",
        "preferencias": ["pintura de cabelo", "hidratação"],
        "visitas": [
            {"data": "2025-07-02", "serviço": "pintura de cabelo"},
            {"data": "2025-06-10", "serviço": "hidratação"}
        ],
        "ultimaVisita": "2025-07-02",
        "valorGastoTotal": 900.00
    }
]


servicos = db["servicos"]

servicos_exemplos = [
    {"nome": "Corte de cabelo", "preco": 120.00, "duracaoMinutos": 45},
    {"nome": "Hidratação", "preco": 80.00, "duracaoMinutos": 30},
    {"nome": "Manicure", "preco": 50.00, "duracaoMinutos": 40},
    {"nome": "Pintura de cabelo", "preco": 200.00, "duracaoMinutos": 90},
    {"nome": "Escova", "preco": 100.00, "duracaoMinutos": 60}
]


campanhas = db["campanhas"]

campanhas_exemplos = [
    {
        "nome": "Verão 2025",
        "descricao": "Desconto de 20% em hidratação para clientes frequentes",
        "dataInicio": "2025-12-01",
        "dataFim": "2026-02-28",
        "segmento": "clientes frequentes",
        "status": "ativa"
    },
    {
        "nome": "Promoção Manicure",
        "descricao": "Desconto especial de 15% em manicure para novas clientes",
        "dataInicio": "2025-07-01",
        "dataFim": "2025-07-31",
        "segmento": "novas clientes",
        "status": "inativa"
    },
    {
        "nome": "Black Friday",
        "descricao": "Pacotes promocionais para cortes e coloração",
        "dataInicio": "2025-11-25",
        "dataFim": "2025-11-30",
        "segmento": "todos os clientes",
        "status": "planejada"
    },
    {
        "nome": "Natal",
        "descricao": "Kit manicure + hidratação com desconto especial",
        "dataInicio": "2025-12-15",
        "dataFim": "2025-12-31",
        "segmento": "clientes VIP",
        "status": "planejada"
    },
    {
        "nome": "Aniversário do Salão",
        "descricao": "Ofertas especiais em todos os serviços durante o mês",
        "dataInicio": "2025-08-01",
        "dataFim": "2025-08-31",
        "segmento": "todos os clientes",
        "status": "ativa"
    }
]


feedbacks = db["feedbacks"]

feedbacks_exemplos = [
    {
        "cliente_email": "maria.oliveira@email.com",
        "servico": "corte",
        "nota": 5,
        "comentario": "Excelente atendimento e corte perfeito!",
        "data": "2025-07-10"
    },
    {
        "cliente_email": "ana.silva@email.com",
        "servico": "manicure",
        "nota": 4,
        "comentario": "Gostei muito do serviço, porém demorou um pouco.",
        "data": "2025-07-12"
    },
    {
        "cliente_email": "carla.mendes@email.com",
        "servico": "hidratação",
        "nota": 5,
        "comentario": "Meu cabelo ficou super hidratado, recomendo!",
        "data": "2025-07-08"
    },
    {
        "cliente_email": "juliana.costa@email.com",
        "servico": "escova",
        "nota": 3,
        "comentario": "Serviço ok, poderia ser mais rápido.",
        "data": "2025-07-05"
    },
    {
        "cliente_email": "patricia.gomes@email.com",
        "servico": "pintura de cabelo",
        "nota": 5,
        "comentario": "Adorei a cor e o atendimento, voltarei!",
        "data": "2025-07-02"
    }
]



agendamentos = db["agendamentos"]

agendamentos_exemplos = [
    {
        "cliente_email": "maria.oliveira@email.com",
        "servico": "corte",
        "dataHora": "2025-08-10T14:00:00",
        "funcionario": "Ana",
        "status": "confirmado"
    },
    {
        "cliente_email": "ana.silva@email.com",
        "servico": "manicure",
        "dataHora": "2025-08-11T10:30:00",
        "funcionario": "Bianca",
        "status": "confirmado"
    },
    {
        "cliente_email": "carla.mendes@email.com",
        "servico": "hidratação",
        "dataHora": "2025-08-12T09:00:00",
        "funcionario": "Carla",
        "status": "cancelado"
    },
    {
        "cliente_email": "juliana.costa@email.com",
        "servico": "escova",
        "dataHora": "2025-08-13T16:00:00",
        "funcionario": "Diana",
        "status": "confirmado"
    },
    {
        "cliente_email": "patricia.gomes@email.com",
        "servico": "pintura de cabelo",
        "dataHora": "2025-08-14T13:00:00",
        "funcionario": "Elisa",
        "status": "confirmado"
    }
]

