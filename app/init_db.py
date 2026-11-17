from app.db import Base, get_engine

if __name__ == "__main__":
    Base.metadata.create_all(get_engine())
