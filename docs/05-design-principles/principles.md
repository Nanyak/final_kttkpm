# Design Principles

> Updated to match the current project structure: React frontend, Nginx gateway, Django REST microservices, RabbitMQ events, MySQL/PostgreSQL data stores, Neo4j graph recommendations, and FAISS/OpenAI-backed RAG.


## Service Ownership

Each service owns its own persistence model and exposes its own API. Foreign data is stored as ids or snapshots rather than cross-database joins: carts store product snapshots, orders store item snapshots, payments store order ids, and shipments store order/user ids.

## Gateway First

The frontend talks to one public origin, the Nginx gateway on port `8000`. Gateway routing keeps the browser independent from internal container names and service ports.

## Synchronous vs Asynchronous Collaboration

- Use HTTP when a workflow needs an immediate answer: cart validates products, order fetches cart contents, order reduces stock, RAG enriches product ids.
- Use RabbitMQ when a state change can be consumed asynchronously: order creation, payment completion/failure/refund, and shipment creation/status updates.

## Authentication

User Service issues stateless JWT access and refresh tokens. Commerce services decode access tokens locally using the shared `JWT_SECRET`; protected internal operations use `X-Internal-Token`.

## Data Consistency

The checkout path favors pragmatic service-level consistency:

- Order creation is transactional inside Order Service.
- Product stock is reduced through Product Service before the order is finalized.
- Cart conversion is best-effort after order creation.
- Payment and shipping updates arrive by event and update order state later.

## AI Design

Recommendation quality is built from multiple independent signals:

- Sequence model scores from recent user behavior.
- Neo4j graph scores from product/user relationships.
- RAG semantic scores from product text and graph-expanded context.

The weights are configurable with `SEQUENCE_MODEL_WEIGHT`, `GRAPH_WEIGHT`, and `RAG_WEIGHT`.

## Operational Boundaries

The system is intended to run with Docker Compose. Databases, RabbitMQ, Redis, Neo4j, Django services, workers, frontend, and gateway are declared in `docker-compose.yml`. Memory limits are configurable through environment variables.
