from sqlalchemy import engine # connect to db
from sqlalchemy.orm import sessionmaker #factory create sqlalchemy session
from env import env
from redis import Redis

db = engine.create_engine(
    #default driver to connect PostgreSQL is psycopg2  
    #postgresql+pyscopg2://{env.DB_USER}:{env.DB_PASSWORD}@{env.DB_HOST}:{env.DB_PORT}/{env.DB_NAME}
    f'postgresql://{env.DB_USER}:{env.DB_PASSWORD}@{env.DB_HOST}:{env.DB_PORT}/{env.DB_NAME}', # format postgresql://user:password@host:port/dbname
    echo=True, ##echo enable logging to see what happening during queries in terminal
    pool_pre_ping=True # check connection before each query
)
##'postgresql+psycopg2://testuser:testpassword@localhost:5432/testuser'
vector_db_conn_str = f'postgresql+psycopg://{env.DB_USER}:{env.DB_PASSWORD}@{env.DB_HOST}:{env.DB_PORT}/{env.DB_NAME}' # connection string for vector db, version 3 of psycopg2
Session = sessionmaker(bind=db) # create a session factory

#connect to redis server
redis = Redis(
    host = env.REDIS_HOST,
    port = env.REDIS_PORT,
    password = env.REDIS_PASSWORD,
    decode_responses=True
)