from collections.abc import Iterator
from functools import lru_cache
from os import environ

from sqlalchemy import String, create_engine
from sqlalchemy.engine import URL, Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class Wish(Base):
    __tablename__ = "wishes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120))


@lru_cache
def get_engine() -> Engine:
    url = URL.create(
        "postgresql+psycopg",
        username=environ.get("POSTGRES_USER", "wishlist"),
        password=environ["POSTGRES_PASSWORD"],
        host=environ.get("POSTGRES_HOST", "127.0.0.1"),
        port=int(environ.get("POSTGRES_PORT", "5432")),
        database=environ.get("POSTGRES_DB", "wishlist"),
        query={"connect_timeout": "3"},
    )
    return create_engine(url, pool_pre_ping=True)


def get_session() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session
