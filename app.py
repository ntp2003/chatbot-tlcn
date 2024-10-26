from chainlit_process.authentication import *
from chainlit_process.message import *
import alembic.config

alembic.config.main(argv=["--raiseerr", "upgrade", "head"])
