from app.models.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.pg_config import get_pg_config

config = get_pg_config()

SQLALCHEMY_DATABASE_URL = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['dbname']}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables_on_startup():
    Base.metadata.create_all(bind=engine)
