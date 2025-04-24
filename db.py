from sqlalchemy import engine
from sqlalchemy.orm import sessionmaker
from env import env
from redis import Redis

db = engine.create_engine(
    #default driver to connect PostgreSQL is psycopg2  
    #postgresql+pyscopg2://{env.DB_USER}:{env.DB_PASSWORD}@{env.DB_HOST}:{env.DB_PORT}/{env.DB_NAME}
    f"postgresql://{env.DB_USER}:{env.DB_PASSWORD}@{env.DB_HOST}:{env.DB_PORT}/{env.DB_NAME}",
    echo=False,
    pool_pre_ping=True,
)

#'postgresql+psycopg2://db_user:db_password@localhost:5432/db_name'
vectordb_conn_str = f"postgresql+psycopg://{env.DB_USER}:{env.DB_PASSWORD}@{env.DB_HOST}:{env.DB_PORT}/{env.DB_NAME}"
Session = sessionmaker(db)

#connect to redis server
redis = Redis(
    host=env.REDIS_HOST,
    port=env.REDIS_PORT,
    password=env.REDIS_PASSWORD,
    decode_responses=True,
)
