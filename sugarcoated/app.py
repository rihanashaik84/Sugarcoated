from flask import Flask, request, jsonify
from analyzer import load_red_flags, analyze_ingredients
import json


app = Flask(__name__)


# Load red-flag ingredients
red_flags = load_red_flags(
    "data/redflag_ingredients.csv"
)


# Load products
with open(
    "data/products.json",
    "r",
    encoding="utf-8"
) as file:
    products = json.load(file)


# Home
@app.route("/")
def home():
    return {
        "message": "Sugarcoated API is running"
    }


# Analyze ingredients
@app.route("/analyze", methods=["POST"])
def analyze():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is missing"
        }), 400

    ingredients = data.get("ingredients")

    if not ingredients:
        return jsonify({
            "error": "Ingredients are required"
        }), 400

    if not isinstance(ingredients, str):
        return jsonify({
            "error": "Ingredients must be a string"
        }), 400

    result = analyze_ingredients(
        ingredients,
        red_flags
    )

    return jsonify(result)


# Get one product
@app.route("/product/<product_id>", methods=["GET"])
def get_product(product_id):

    for product in products:

        if product["product_id"] == product_id:
            return jsonify(product)

    return jsonify({
        "error": "Product not found"
    }), 404


# Search products
@app.route("/products", methods=["GET"])
def get_products():

    query = request.args.get("q", "").strip().lower()

    if not query:
        return jsonify(products)

    results = []

    for product in products:

        name = product["name"].lower()
        brand = product["brand"].lower()

        if query in name or query in brand:
            results.append(product)

    return jsonify(results)


# Health check
@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "status": "ok",
        "products_loaded": len(products),
        "red_flags_loaded": len(red_flags)
    })


if __name__ == "__main__":
    app.run(debug=True)