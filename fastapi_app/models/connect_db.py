from fastapi_app.models.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi_app.services.pg_config import get_pg_config
import psycopg

config = get_pg_config()

SQLALCHEMY_DATABASE_URL = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['dbname']}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables_on_startup():
    Base.metadata.create_all(bind=engine)

def connect_to_postgres():
    """Connect to a PostgreSQL database.
    
    This method establishes a connection to a PostgreSQL database using the provided
    database credentials and connection parameters.
    
    Returns:
        psycopg.Connection: A connection object to the PostgreSQL database.
    
    Raises:
        Exception: If there is an error while attempting to connect to the database,
        an exception is raised with a descriptive error message.
    """
    
    try:
        return psycopg.connect(
            dbname=config['dbname'],
            user=config['user'],
            password=config['password'],
            host=config['host'],
            port=config['port'],
        )
    except Exception as e:
        raise Exception(f"Database connection error: {e}")
