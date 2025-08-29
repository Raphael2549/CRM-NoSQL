# BeautySalon Marketing System

Este sistema tem como objetivo auxiliar salões de beleza femininos no planejamento de **campanhas de marketing**, utilizando dados armazenados em um **banco de dados NoSQL**.

A partir das informações dos clientes, o sistema identifica padrões de consumo, preferências e frequência de visitas, facilitando ações promocionais personalizadas.

---

## Objetivo

Criar um sistema inteligente que utiliza um banco NoSQL para:
- Armazenar dados de clientes do salão;
- Analisar padrões de comportamento;
- Gerar campanhas promocionais e de fidelização;
- Automatizar ações de marketing.

---

## Tecnologias Utilizadas

- **Banco de Dados**: MongoDB (ou outro NoSQL como Firebase, CouchDB, etc.)
- **Backend**: Node.js / Python / outro (dependendo da stack escolhida)
- **APIs**: E-mail, WhatsApp, SMS (para envio de promoções)
- **Dashboard**: (opcional) React, Vue, ou HTML/CSS para visualização de dados

---

## Estrutura de Dados (Exemplo em MongoDB)

### `clientes`
```json
{
  "nome": "Maria Oliveira",
  "email": "maria.oliveira@email.com",
  "telefone": "11999999999",
  "dataNascimento": "1985-05-20",
  "preferencias": ["corte", "hidratação", "manicure"],
  "visitas": [
    { "data": "2025-07-10", "serviço": "corte" },
    { "data": "2025-06-05", "serviço": "hidratação" }
  ],
  "ultimaVisita": "2025-07-10",
  "valorGastoTotal": 850.00
}

Com certeza. Aqui está o texto completo, formatado em Markdown, pronto para você copiar e colar diretamente no seu arquivo README.md.

(Copie tudo a partir da linha abaixo)

Atividade 04/09 (Estrutura de Dados Avançada do Redis)
Para esta atividade, foi implementada a estrutura de dados Redis Bitmap para criar uma funcionalidade de campanha em tempo real, que rastreia e limita uma promoção diária para os primeiros 5 clientes únicos.

O que é Redis Bitmap?
É uma estrutura de dados extremamente eficiente em termos de memória que permite rastrear informações binárias (sim/não, ativo/inativo) para milhões de usuários. Cada usuário é mapeado para um "bit" em uma longa sequência, e podemos ligar ou desligar esse bit para registrar uma ação, usando comandos como SETBIT, GETBIT e BITCOUNT.

Como foi implementado?
A lógica foi dividida em duas partes principais no arquivo main.py: a escrita (quando um cliente participa da promoção) e a leitura (para consultar o status da campanha).

1. Registrando a Participação (A Escrita)
A lógica de escrita é acionada por uma ação de negócio crucial: a conclusão de um agendamento.

Gatilho: Dentro do endpoint PUT /agendamentos/{id}/status, quando o status é alterado para "Concluído".

Mapeamento de Clientes: Como Bitmaps requerem IDs numéricos, o sistema utiliza um Hash do Redis (email_para_id) para criar um mapeamento permanente entre o e-mail do cliente e um ID numérico único (gerado por um contador INCR do Redis, proximo_id_cliente).

Lógica Condicional: Antes de registrar, o sistema verifica se a meta de 5 clientes únicos já foi atingida naquele dia usando BITCOUNT. Se a meta estiver em aberto e aquele cliente específico ainda não tiver sido registrado (verificado com GETBIT), o sistema executa o SETBIT, marcando o cliente como participante.

Trecho do endpoint PUT /agendamentos/{id}/status em main.py:

Python

# ... (dentro do if status.lower() in ["concluido", "concluído"])
try:
    meta_do_dia = 5
    chave_meta = f"meta_diaria:{data_hora_obj.strftime('%Y-%m-%d')}"
    
    # Pega ou cria o ID numérico do cliente
    id_cliente = redis_client.hget("email_para_id", cliente_email)
    if id_cliente is None:
        id_cliente = redis_client.incr("proximo_id_cliente")
        redis_client.hset("email_para_id", cliente_email, id_cliente)
    
    id_cliente = int(id_cliente)

    # Verifica se o cliente já participou hoje
    ja_veio_hoje = redis_client.getbit(chave_meta, id_cliente)

    if ja_veio_hoje == 0:
        contagem_atual = redis_client.bitcount(chave_meta)
        if contagem_atual < meta_do_dia:
            # Marca o cliente no bitmap
            redis_client.setbit(chave_meta, id_cliente, 1)
            # Adiciona mensagem de sucesso na resposta da API
            mensagem_retorno["promocao_diaria"] = f"Parabéns! Este foi o cliente único número {contagem_atual + 1} de {meta_do_dia}."
# ...
2. Consultando o Status da Campanha (A Leitura)
Foi criado um endpoint dedicado para que a equipe do salão possa consultar o andamento da promoção em tempo real.

Endpoint: GET /campanhas/meta-diaria

Lógica: Este endpoint simplesmente usa o comando BITCOUNT na chave do dia solicitado (ex: meta_diaria:2025-08-29) para contar quantos bits estão ligados (quantos clientes únicos já participaram). Com base nesse número, ele retorna um JSON com o status atual da campanha.

Trecho do endpoint GET /campanhas/meta-diaria em main.py:

Python

@app.get("/campanhas/meta-diaria")
def get_daily_goal_status(data: Optional[str] = None):
    # ...
    if data is None:
        data = datetime.now().strftime("%Y-%m-%d")
    
    chave_meta = f"meta_diaria:{data}"
    
    # Conta quantos clientes únicos foram atendidos na data
    clientes_atendidos = redis_client.bitcount(chave_meta)
    
    return {
        "data": data,
        "meta_clientes_unicos": 5,
        "clientes_atingidos_hoje": clientes_atendidos,
        # ...
    }
Resultado Final
Essa implementação adiciona uma funcionalidade de negócio interativa e de alto valor, utilizando uma estrutura de dados avançada do Redis de forma eficiente e robusta. O sistema é resiliente a reinicializações (devido à facilidade de reconstruir a métrica diária a partir do MongoDB) e protege o banco de dados principal de consultas complexas, ao mesmo tempo em que fornece feedback em tempo real para o usuário da API.
