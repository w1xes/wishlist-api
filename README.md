# Wishlist API

FastAPI-застосунок для списку бажань. SQLAlchemy зберігає записи в Postgres. `/ready` перевіряє зв’язок із Postgres і Redis, а `/health` перевіряє лише доступність API.

```powershell
Copy-Item .env.example .env
docker compose up -d --wait
```

Документація Swagger доступна за адресою [127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). `GET /items` читає список, `POST /items` додає бажання з полем `title`, а `DELETE /items/{id}` видаляє запис.
