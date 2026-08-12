import os
import sys

import pytest
from peewee import SqliteDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import ProductModel  # noqa: E402
from app import app as flask_app  # noqa: E402

# All tests run against an in-memory database, the real products.db is untouched
test_db = SqliteDatabase(":memory:")


@pytest.fixture(autouse=True)
def database():
    """A fresh, empty database for every test."""
    test_db.bind([ProductModel], bind_refs=False, bind_backrefs=False)
    test_db.connect(reuse_if_open=True)
    test_db.create_tables([ProductModel])
    yield test_db
    test_db.drop_tables([ProductModel])
    test_db.close()


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as test_client:
        yield test_client


@pytest.fixture
def sample_products():
    """Three products stored in the database."""
    from db import create_product

    return [
        create_product("Sugar", 32),
        create_product("Bread", 20),
        create_product("Milk", 32),
    ]
