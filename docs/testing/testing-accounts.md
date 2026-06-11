# Testing Accounts

Demo accounts are seeded by `user_service/apps/users/management/commands/seed_demo_accounts.py`.

| Role | Username | Password | Notes |
|---|---|---|---|
| Admin | `admin` | `admin123` | Can access admin user, order, and shipping list endpoints. |
| Customer | `alice` | `password123` | General shopping flow account. |
| Customer | `bob` | `password123` | General shopping flow account. |

Seed products with:

```bash
docker compose exec product_service python manage.py seed_demo_products
```

Seed demo accounts with:

```bash
docker compose exec user_service python manage.py seed_demo_accounts
```

Use the gateway at `http://localhost:8000` for browser and API testing.

