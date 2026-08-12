import os
import subprocess
import sys

import pytest

from db import (ProductModel,
                create_product,
                get_product_by_id,
                update_product,
                delete_product,
                _add_default_data,
                _print_all_data)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestProductModel:
    def test_to_dict(self):
        product = create_product("Sugar", 32)

        assert product.to_dict() == {"id": product.id, "name": "Sugar", "price": 32}

    def test_str(self):
        product = create_product("Sugar", 32)

        assert str(product) == f"({product.id}, Sugar, 32)"


class TestCreateProduct:
    def test_returns_saved_product(self):
        product = create_product("Sugar", 32)

        assert product.id is not None
        assert product.name == "Sugar"
        assert product.price == 32

    def test_persisted_in_database(self):
        product = create_product("Sugar", 32)

        stored = ProductModel.get(ProductModel.id == product.id)
        assert stored.name == "Sugar"
        assert stored.price == 32

    def test_ids_are_unique(self):
        first = create_product("Sugar", 32)
        second = create_product("Bread", 20)

        assert first.id != second.id
        assert ProductModel.select().count() == 2


class TestGetProductById:
    def test_existing_product(self, sample_products):
        expected = sample_products[0]

        product = get_product_by_id(expected.id)

        assert product is not None
        assert product.id == expected.id
        assert product.name == "Sugar"

    def test_missing_product_returns_none(self):
        assert get_product_by_id(9999) is None

    def test_missing_product_in_empty_database(self):
        assert get_product_by_id(1) is None


class TestUpdateProduct:
    def test_update_name_only(self, sample_products):
        product = sample_products[0]

        updated = update_product(product.id, name="Sugar (1kg)")

        assert updated.name == "Sugar (1kg)"
        assert get_product_by_id(product.id).name == "Sugar (1kg)"
        assert get_product_by_id(product.id).price == 32

    def test_update_price_only(self, sample_products):
        product = sample_products[0]

        updated = update_product(product.id, price=35)

        assert updated.price == 35
        assert get_product_by_id(product.id).name == "Sugar"
        assert get_product_by_id(product.id).price == 35

    def test_update_both_fields(self, sample_products):
        product = sample_products[0]

        update_product(product.id, name="Sugar (1kg)", price=35)

        stored = get_product_by_id(product.id)
        assert stored.name == "Sugar (1kg)"
        assert stored.price == 35

    def test_update_without_fields_keeps_values(self, sample_products):
        product = sample_products[0]

        updated = update_product(product.id)

        assert updated.name == "Sugar"
        assert updated.price == 32

    def test_update_missing_product_returns_none(self):
        assert update_product(9999, name="Ghost") is None


class TestDeleteProduct:
    def test_delete_existing_product(self, sample_products):
        product = sample_products[0]

        assert delete_product(product.id) is True
        assert get_product_by_id(product.id) is None
        assert ProductModel.select().count() == len(sample_products) - 1

    def test_delete_missing_product_returns_false(self):
        assert delete_product(9999) is False

    def test_delete_does_not_touch_other_products(self, sample_products):
        delete_product(sample_products[0].id)

        assert get_product_by_id(sample_products[1].id) is not None


class TestHelpers:
    def test_add_default_data(self):
        _add_default_data()

        names = [product.name for product in ProductModel.select()]
        assert names == ["Sugar", "Sult", "Bread", "Butter", "Milk"]

    def test_print_all_data(self, capsys, sample_products):
        _print_all_data()

        output = capsys.readouterr().out
        assert "Sugar" in output
        assert "Bread" in output
        assert "Milk" in output

    def test_print_all_data_empty_database(self, capsys):
        _print_all_data()

        assert capsys.readouterr().out == ""


@pytest.mark.parametrize("flags, expected", [
    (["-a", "-p"], ["Sugar", "Sult", "Bread", "Butter", "Milk"]),
    (["--add_default_data", "--print_all_data"], ["Sugar", "Milk"]),
])
def test_cli_adds_and_prints_data(tmp_path, flags, expected):
    """db.py run as a CLI creates the table and fills it with data."""
    result = subprocess.run(
        [sys.executable, os.path.join(PROJECT_ROOT, "db.py"), *flags],
        cwd=tmp_path, capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stderr
    for name in expected:
        assert name in result.stdout
    assert (tmp_path / "products.db").exists()


def test_cli_deletes_all_data(tmp_path):
    db_script = os.path.join(PROJECT_ROOT, "db.py")
    subprocess.run([sys.executable, db_script, "-a"], cwd=tmp_path, check=True)

    result = subprocess.run(
        [sys.executable, db_script, "-d", "-p"],
        cwd=tmp_path, capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == ""
