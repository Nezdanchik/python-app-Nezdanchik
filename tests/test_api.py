from db import ProductModel, get_product_by_id


class TestGetProducts:
    def test_empty_database_returns_empty_list(self, client):
        response = client.get("/api/products")

        assert response.status_code == 200
        assert response.get_json() == []

    def test_returns_all_products(self, client, sample_products):
        response = client.get("/api/products")

        assert response.status_code == 200
        body = response.get_json()
        assert len(body) == 3
        assert body[0] == {"id": sample_products[0].id, "name": "Sugar", "price": 32}
        assert [item["name"] for item in body] == ["Sugar", "Bread", "Milk"]


class TestPostProduct:
    def test_creates_product(self, client):
        response = client.post("/api/products", json={"name": "Eggs", "price": 12.0})

        assert response.status_code == 201
        body = response.get_json()
        assert body["message"] == "Product added successfully."
        assert body["productId"] is not None

        stored = get_product_by_id(body["productId"])
        assert stored.name == "Eggs"
        assert stored.price == 12

    def test_form_data_is_not_supported(self, client):
        """The API only accepts JSON: form-data is rejected with 415."""
        response = client.post("/api/products", data={"name": "Eggs", "price": "12.0"})

        assert response.status_code == 415
        assert ProductModel.select().count() == 0

    def test_missing_name_returns_400(self, client):
        response = client.post("/api/products", json={"price": 12.0})

        assert response.status_code == 400
        assert "name" in response.get_json()["message"]
        assert ProductModel.select().count() == 0

    def test_missing_price_returns_400(self, client):
        response = client.post("/api/products", json={"name": "Eggs"})

        assert response.status_code == 400
        assert "price" in response.get_json()["message"]

    def test_empty_body_returns_400(self, client):
        response = client.post("/api/products", json={})

        assert response.status_code == 400

    def test_non_numeric_price_returns_400(self, client):
        response = client.post("/api/products", json={"name": "Eggs", "price": "free"})

        assert response.status_code == 400
        assert ProductModel.select().count() == 0


class TestGetProduct:
    def test_returns_product(self, client, sample_products):
        product = sample_products[0]

        response = client.get(f"/api/products/{product.id}")

        assert response.status_code == 200
        assert response.get_json() == {"id": product.id, "name": "Sugar", "price": 32}

    def test_missing_product_returns_404(self, client):
        response = client.get("/api/products/9999")

        assert response.status_code == 404
        assert response.get_json() == {"error": "Product not found."}

    def test_non_integer_id_returns_404(self, client):
        assert client.get("/api/products/abc").status_code == 404


class TestPatchProduct:
    def test_updates_name_and_price(self, client, sample_products):
        product = sample_products[0]

        response = client.patch(
            f"/api/products/{product.id}",
            json={"name": "Sugar (1kg)", "price": 35.0},
        )

        assert response.status_code == 200
        assert response.get_json() == {"message": "Product updated successfully."}
        stored = get_product_by_id(product.id)
        assert stored.name == "Sugar (1kg)"
        assert stored.price == 35

    def test_updates_name_only(self, client, sample_products):
        product = sample_products[0]

        response = client.patch(f"/api/products/{product.id}", json={"name": "Sugar (1kg)"})

        assert response.status_code == 200
        stored = get_product_by_id(product.id)
        assert stored.name == "Sugar (1kg)"
        assert stored.price == 32

    def test_updates_price_only(self, client, sample_products):
        product = sample_products[0]

        response = client.patch(f"/api/products/{product.id}", json={"price": 35.0})

        assert response.status_code == 200
        stored = get_product_by_id(product.id)
        assert stored.name == "Sugar"
        assert stored.price == 35

    def test_empty_body_keeps_product_unchanged(self, client, sample_products):
        product = sample_products[0]

        response = client.patch(f"/api/products/{product.id}", json={})

        assert response.status_code == 200
        stored = get_product_by_id(product.id)
        assert stored.name == "Sugar"
        assert stored.price == 32

    def test_missing_product_returns_404(self, client):
        response = client.patch("/api/products/9999", json={"name": "Ghost"})

        assert response.status_code == 404
        assert response.get_json() == {"error": "Product not found."}

    def test_non_numeric_price_returns_400(self, client, sample_products):
        product = sample_products[0]

        response = client.patch(f"/api/products/{product.id}", json={"price": "free"})

        assert response.status_code == 400
        assert get_product_by_id(product.id).price == 32


class TestDeleteProduct:
    def test_deletes_product(self, client, sample_products):
        product = sample_products[0]

        response = client.delete(f"/api/products/{product.id}")

        assert response.status_code == 200
        assert response.get_json() == {"message": "Product deleted."}
        assert get_product_by_id(product.id) is None
        assert ProductModel.select().count() == 2

    def test_missing_product_returns_404(self, client):
        response = client.delete("/api/products/9999")

        assert response.status_code == 404
        assert response.get_json() == {"error": "Product not found."}

    def test_delete_twice_returns_404(self, client, sample_products):
        product_id = sample_products[0].id
        client.delete(f"/api/products/{product_id}")

        assert client.delete(f"/api/products/{product_id}").status_code == 404


class TestCors:
    def test_cors_header_on_api_route(self, client):
        """origins="*" allows any origin, flask-cors echoes it back in the response."""
        response = client.get("/api/products", headers={"Origin": "http://example.com"})

        assert response.headers["Access-Control-Allow-Origin"] == "http://example.com"

    def test_no_cors_header_outside_api(self, client):
        response = client.get("/", headers={"Origin": "http://example.com"})

        assert "Access-Control-Allow-Origin" not in response.headers
