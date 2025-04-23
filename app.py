from chainlit_process.authentication import *
from chainlit_process.message import *
import alembic.config
from literalai import LiteralClient
from env import env
import subprocess
from chainlit_process.data_layer import DataLayer
import chainlit.data as cl_data


client = LiteralClient(api_key=env.LITERAL_KEY)
client.instrument_openai()
rq_command = ["rq", "worker", "--with-scheduler"]
rq_process = subprocess.Popen(
    rq_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
)
alembic.config.main(argv=["--raiseerr", "upgrade", "head"])


def set_data_layer():
    if not cl_data._data_layer:
        cl_data._data_layer = DataLayer()


set_data_layer()
