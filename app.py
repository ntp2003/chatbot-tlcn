from chainlit_process.authentication import *
from chainlit_process.message import *
import alembic.config
from literalai import LiteralClient
from env import env
import subprocess


client = LiteralClient(api_key=env.LITERAL_API_KEY)
client.instrument_openai()
command = ["rq", "worker", "--with-scheduler"]
process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
alembic.config.main(argv=["--raiseerr", "upgrade", "head"])
