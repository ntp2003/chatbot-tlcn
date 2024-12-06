from chainlit_process.authentication import *
from chainlit_process.message import *
import alembic.config
from literalai import LiteralClient
from env import env
import subprocess


client = LiteralClient(api_key=env.LITERAL_API_KEY)
client.instrument_openai()
rq_command = ["rq", "worker", "--with-scheduler"]
rq_process = subprocess.Popen(
    rq_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
)
alembic.config.main(argv=["--raiseerr", "upgrade", "head"])
