import json
import pytest
from pathlib import Path


SAMPLE_DATA = {
    "trendy.catalog.products": {
        "product_id": "PROD_US_78234",
        "sku": "DRS-BLK-M-001",
        "brand": "Everlane",
        "category": "dresses",
        "price_usd": 98.0,
        "attributes": {
            "size": "M",
            "color": "black",
            "material": "ECOVERO",
        },
        "inventory": {
            "in_stock": True,
            "units_available": 42,
        },
    },
    "trendy.orders.purchases": {
        "order_id": "ORD_US_5512893",
        "customer_id": "CUST_US_109823",
        "status": "SHIPPED",
        "total_usd": 143.50,
        "shipping": {
            "address": "350 5th Ave",
            "city": "New York",
            "state": "NY",
            "zip": "10118",
        },
    },
}

SCHEMA_DATA = {
    "trendy.catalog.products": [
        {"name": "product_id", "type": "STRING", "description": "Unique product identifier"},
        {"name": "sku", "type": "STRING", "description": "Stock keeping unit code"},
        {"name": "brand", "type": "STRING", "description": "Brand name"},
        {"name": "category", "type": "STRING", "description": "Product category (dresses, tops, pants, etc.)"},
        {"name": "price_usd", "type": "FLOAT", "description": "Retail price in USD"},
        {"name": "attributes", "type": "RECORD", "description": "Size, color, and material attributes"},
        {"name": "inventory", "type": "RECORD", "description": "Stock availability and unit count"},
        {"name": "updated_at", "type": "TIMESTAMP", "description": "Last catalog update timestamp"},
    ],
    "trendy.orders.purchases": [
        {"name": "order_id", "type": "STRING", "description": "Unique order identifier"},
        {"name": "customer_id", "type": "STRING", "description": "Customer foreign key"},
        {"name": "status", "type": "STRING", "description": "Order lifecycle status (PLACED, SHIPPED, DELIVERED, RETURNED)"},
        {"name": "total_usd", "type": "FLOAT", "description": "Order total in USD"},
        {"name": "shipping", "type": "RECORD", "description": "US shipping address details"},
        {"name": "updated_at", "type": "TIMESTAMP", "description": "Last order update timestamp"},
    ],
}


@pytest.fixture
def json_files(tmp_path: Path) -> tuple[Path, Path]:
    samples_path = tmp_path / "sample_records.json"
    schemas_path = tmp_path / "schemas.json"
    samples_path.write_text(json.dumps(SAMPLE_DATA))
    schemas_path.write_text(json.dumps(SCHEMA_DATA))
    return samples_path, schemas_path
