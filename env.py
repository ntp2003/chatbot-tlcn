import os
from dotenv import load_dotenv
from pydantic import BaseModel


load_dotenv(".env")


class Env(BaseModel):
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    OPENAI_API_KEY: str

env = Env.model_validate(os.environ)
