import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "api"))

import pytest
from sqlalchemy.orm import Session

from app.db.session import engine


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()

    db = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield db
    finally:
        db.close()
        transaction.rollback()
        connection.close()
