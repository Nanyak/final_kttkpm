# Payment Service API

> Updated to match the current project structure: React frontend, Nginx gateway, Django REST microservices, RabbitMQ events, MySQL/PostgreSQL data stores, Neo4j graph recommendations, and FAISS/OpenAI-backed RAG.


Base path: `/api` through `payment_service:8005`.

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/payments/` | Bearer | List current user's payments. |
| POST | `/api/payments/` | Bearer | Create and process payment. |
| POST | `/api/payments/webhook/vnpay/` | Gateway callback | Handle simplified VNPay IPN callback. |
| GET | `/api/payments/{id}/` | Owner/admin | Payment detail. |
| GET | `/api/payments/{id}/receipt/` | Owner/admin | Receipt summary. |
| POST | `/api/payments/{id}/refund/` | Owner/admin | Create refund with `refund_amount` and `reason`. |

Supported methods: `cod`, `vnpay`, `momo`, `credit_card`, `bank_transfer`. Non-COD payments are simulated with a success/failure gateway response and publish payment events.

