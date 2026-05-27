import json
import pytest
from pathlib import Path


DATA_SOURCES = {
    "trendy.catalog.products": {
        "fields": [
            {"name": "product_id", "type": "STRING", "description": "Unique product identifier", "null_pct": 0.0, "n_distinct": 100, "example": "PROD_US_78234"},
            {"name": "sku", "type": "STRING", "description": "Stock keeping unit code", "null_pct": 0.0, "n_distinct": 100, "example": "DRS-BLK-M-001"},
            {"name": "brand", "type": "STRING", "description": "Brand name", "null_pct": 0.0, "n_distinct": 10, "example": "Everlane"},
            {"name": "category", "type": "STRING", "description": "Product category (dresses, tops, pants, etc.)", "null_pct": 0.0, "n_distinct": 5, "example": "dresses"},
            {"name": "price_usd", "type": "FLOAT", "description": "Retail price in USD", "null_pct": 0.0, "n_distinct": 50, "example": 98.0},
            {
                "name": "attributes",
                "type": "RECORD",
                "description": "Size, color, and material attributes",
                "null_pct": 0.0,
                "example": {"size": "M", "color": "black", "material": "ECOVERO"},
                "fields": [
                    {"name": "size", "type": "STRING", "description": "Size", "null_pct": 0.0, "example": "M"},
                    {"name": "color", "type": "STRING", "description": "Color", "null_pct": 0.0, "example": "black"},
                    {"name": "material", "type": "STRING", "description": "Material", "null_pct": 0.0, "example": "ECOVERO"},
                ],
            },
            {
                "name": "inventory",
                "type": "RECORD",
                "description": "Stock availability and unit count",
                "null_pct": 0.0,
                "example": {"in_stock": True, "units_available": 42},
                "fields": [
                    {"name": "in_stock", "type": "BOOLEAN", "description": "Whether in stock", "null_pct": 0.0, "example": True},
                    {"name": "units_available", "type": "INTEGER", "description": "Units available", "null_pct": 0.0, "example": 42},
                ],
            },
            {"name": "updated_at", "type": "TIMESTAMP", "description": "Last catalog update timestamp", "null_pct": 0.0, "example": "2024-01-01T00:00:00Z"},
        ]
    },
    "trendy.orders.purchases": {
        "fields": [
            {"name": "order_id", "type": "STRING", "description": "Unique order identifier", "null_pct": 0.0, "n_distinct": 100, "example": "ORD_US_5512893"},
            {"name": "customer_id", "type": "STRING", "description": "Customer foreign key", "null_pct": 0.0, "n_distinct": 80, "example": "CUST_US_109823"},
            {"name": "status", "type": "STRING", "description": "Order lifecycle status (PLACED, SHIPPED, DELIVERED, RETURNED)", "null_pct": 0.0, "n_distinct": 5, "example": "SHIPPED"},
            {"name": "total_usd", "type": "FLOAT", "description": "Order total in USD", "null_pct": 0.0, "n_distinct": 50, "example": 143.50},
            {
                "name": "shipping",
                "type": "RECORD",
                "description": "US shipping address details",
                "null_pct": 0.0,
                "example": {"address": "350 5th Ave", "city": "New York", "state": "NY", "zip": "10118"},
                "fields": [
                    {"name": "address", "type": "STRING", "description": "Street address", "null_pct": 0.0, "example": "350 5th Ave"},
                    {"name": "city", "type": "STRING", "description": "City", "null_pct": 0.0, "example": "New York"},
                    {"name": "state", "type": "STRING", "description": "State", "null_pct": 0.0, "example": "NY"},
                    {"name": "zip", "type": "STRING", "description": "ZIP code", "null_pct": 0.0, "example": "10118"},
                ],
            },
            {"name": "updated_at", "type": "TIMESTAMP", "description": "Last order update timestamp", "null_pct": 0.0, "example": "2024-01-01T00:00:00Z"},
        ]
    },
}


@pytest.fixture
def data_sources(tmp_path: Path) -> Path:
    path = tmp_path / "data_sources.json"
    path.write_text(json.dumps(DATA_SOURCES))
    return path
