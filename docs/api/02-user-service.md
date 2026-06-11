# User Service API

> Updated to match the current project structure: React frontend, Nginx gateway, Django REST microservices, RabbitMQ events, MySQL/PostgreSQL data stores, Neo4j graph recommendations, and FAISS/OpenAI-backed RAG.


Base path: `/api` through `user_service:8002`.

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register/` | No | Register a customer account. |
| POST | `/api/auth/login/` | No | Return `access`, `refresh`, and user profile. |
| POST | `/api/auth/refresh/` | Refresh token | Return a new access token. |
| POST | `/api/auth/logout/` | No | Stateless logout acknowledgement. |
| GET | `/api/users/me/` | Bearer | Current user profile. |
| PATCH | `/api/users/me/` | Bearer | Update `first_name`, `last_name`, `phone_number`, or `email`. |
| POST | `/api/users/me/change-password/` | Bearer | Change password with `old_password` and `new_password`. |
| GET | `/api/users/me/addresses/` | Bearer | List own addresses. |
| POST | `/api/users/me/addresses/` | Bearer | Create address. |
| GET/PATCH/DELETE | `/api/users/me/addresses/{id}/` | Bearer | Manage own address. |
| GET | `/api/users/` | Admin | List users. |
| GET | `/api/users/{id}/` | Admin | Get user detail. |

JWT payloads include `user_id`, `email`, `role`, and token `type`.

