import unittest

from app import app


class TestAPI(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def test_home(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)

    def test_health(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["products_loaded"], 852)
        self.assertEqual(data["red_flags_loaded"], 52)

    def test_analyze(self):
        response = self.client.post(
            "/analyze",
            json={
                "ingredients": "Sugar, Dextrose"
            }
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertIn("SUGAR", data["matched_ingredients"])
        self.assertIn("DEXTROSE", data["matched_ingredients"])

        self.assertEqual(data["score"], 6)

    def test_empty_ingredients(self):
        response = self.client.post(
            "/analyze",
            json={
                "ingredients": ""
            }
        )

        self.assertEqual(response.status_code, 400)

    def test_invalid_ingredients(self):
        response = self.client.post(
            "/analyze",
            json={
                "ingredients": 123
            }
        )

        self.assertEqual(response.status_code, 400)

    def test_product_search(self):
        response = self.client.get(
            "/products?q=amul"
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertIsInstance(data, list)

    def test_product_not_found(self):
        response = self.client.get(
            "/product/999999"
        )

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()