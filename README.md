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
