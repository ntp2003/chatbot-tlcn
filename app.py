from chainlit_process.authentication import *
from chainlit_process.message import *
import alembic.config
from literalai import LiteralClient
from env import env
import subprocess

# Init LiteralClient to  and logging OpenAI API calls
client = LiteralClient(api_key=env.LITERAL_API_KEY)
client.instrument_openai()

# Init RQ worker n scheduler to run background tasks
rq_command = ["rq", "worker", "--with-scheduler"]
rq_process = subprocess.Popen(
    rq_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
)

# Migrate database with alembic
alembic.config.main(argv=["--raiseerr", "upgrade", "head"])
