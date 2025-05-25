from sqlalchemy.sql import text
from db import Session


if __name__ == "__main__":
    with Session() as session:
        print(
            session.execute(text("SELECT 1")).scalar()
        )  # Sử dụng text() để khai báo SQL
