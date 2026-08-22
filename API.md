# Sugarcoated API

Base URL:
```
http://127.0.0.1:5000
```

---

## GET /

Checks whether the API is running.

### Response
```json
{
    "message": "Sugarcoated API is running"
}
```

---

## GET /health

Returns backend status and loaded dataset sizes.

### Response
```json
{
    "products_loaded": 852,
    "red_flags_loaded": 52,
    "status": "ok"
}
```

---

## GET /search?q=<query>

Searches products by name or brand.

### Example
```
/search?q=amul
```

---

## GET /products

Returns all available products.

### Example
```
/products
```

---

## GET /products?q=<query>

Searches products by name or brand.

### Example
```
/products?q=amul
```

---

## GET /product/<product_id>

Returns information about one product.

### Example
```
/product/1
```

---

## GET /product/<product_id>/analysis

Returns the existing ingredient analysis for a product.

### Example
```
/product/1/analysis
```

---

## POST /analyze

Analyzes a custom ingredient list.

### Request
```json
{
    "ingredients": "Sugar, Dextrose, Refined Palm Oil"
}
```

### Response
```json
{
    "matched_categories": [
        "added_sugar",
        "hidden_sugar",
        "saturated_fat_source"
    ],
    "matched_ingredients": [
        "SUGAR",
        "DEXTROSE",
        "REFINED PALM OIL"
    ],
    "matched_severities": [
        "medium",
        "medium",
        "medium"
    ],
    "score": 9,
    "risk_level": "Moderate"
}
```

---

## GET /stats

Returns statistics about the product dataset.

### Response
```json
{
    "total_products": 852,
    "low_risk": 372,
    "moderate_risk": 232,
    "high_risk": 248
}
```

---

## Scoring System

Sugarcoated uses a rule-based severity scoring system.

| Severity | Points |
| -------- | -----: |
| High     |      5 |
| Medium   |      3 |
| Low      |      1 |

### Risk Levels

| Score | Risk Level |
| ----: | ---------- |
|   0–4 | Low        |
|   5–9 | Moderate   |
|   10+ | High       |

These are project-defined rules and are not medical diagnoses or regulatory classifications.

---

## API Workflow

### Existing Product
```
GET /search?q=<query>
    ↓
Select product
    ↓
GET /product/<product_id>/analysis
    ↓
Display analysis
```

### Custom Ingredient List
```
POST /analyze
    ↓
Normalize ingredients
    ↓
Match against red-flag table
    ↓
Calculate score
    ↓
Return risk level
```