from sqlalchemy.sql import text
from db import Session
with Session() as session:
    print(session.execute(text("SELECT 1")).scalar())  # Sử dụng text() để khai báo SQL
