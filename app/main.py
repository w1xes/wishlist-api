from os import environ
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, StringConstraints
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db import Wish, get_engine, get_session

app = FastAPI(title="Wishlist API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[environ.get("UI_ORIGIN", "http://127.0.0.1:5174")],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)

Database = Annotated[Session, Depends(get_session)]


class WishInput(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class WishOutput(WishInput):
    model_config = ConfigDict(from_attributes=True)

    id: int


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def readiness() -> dict[str, str]:
    redis_url = environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        with Redis.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2) as cache:
            cache.ping()
    except (SQLAlchemyError, RedisError) as error:
        raise HTTPException(
            status_code=503, detail="Wishlist dependencies are unavailable"
        ) from error
    return {"postgres": "ok", "redis": "ok"}


@app.get("/items", response_model=list[WishOutput])
def list_items(session: Database) -> list[Wish]:
    return list(session.scalars(select(Wish).order_by(Wish.id.desc())))


@app.post("/items", response_model=WishOutput, status_code=201)
def create_item(item: WishInput, session: Database) -> Wish:
    wish = Wish(title=item.title)
    session.add(wish)
    session.commit()
    session.refresh(wish)
    return wish


@app.delete("/items/{item_id}", status_code=204, response_class=Response)
def delete_item(item_id: int, session: Database) -> Response:
    wish = session.get(Wish, item_id)
    if wish is None:
        raise HTTPException(status_code=404, detail="Wish not found")
    session.delete(wish)
    session.commit()
    return Response(status_code=204)
