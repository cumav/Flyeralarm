from __future__ import annotations

import json
import logging
from typing import Iterable

import typesense

from .config import TypesenseConfig
from .models import OfferBatch, OfferRecord


logger = logging.getLogger(__name__)


class TypesenseWriter:
    def __init__(self, config: TypesenseConfig):
        self.config = config
        self.client = typesense.Client(
            {
                "nodes": [
                    {
                        "host": config.host,
                        "port": config.port,
                        "protocol": config.protocol,
                    }
                ],
                "api_key": config.api_key,
                "connection_timeout_seconds": 5,
            }
        )

    def ensure_schema(self, schema: dict):
        try:
            self.client.collections[schema["name"]].retrieve()
            logger.info("Typesense collection %s already exists", schema["name"])
        except typesense.exceptions.ObjectNotFound:
            logger.info("Creating Typesense collection %s", schema["name"])
            self.client.collections.create(schema)

    def upsert_batch(self, records: Iterable[OfferRecord]):
        documents = [record.__dict__ for record in records]
        if not documents:
            return
        logger.info("Upserting %s offers to Typesense", len(documents))
        # typesense import endpoint supports batch upsert
        payload = "\n".join(json.dumps(doc) for doc in documents)
        self.client.collections[self.config.collection].documents.import_(
            payload, {
                "action": "upsert",
                "batch_size": self.config.batch_size,
            }
        )


OFFERS_SCHEMA = {
    "name": "offers",
    "fields": [
        {"name": "id", "type": "string"},
        {"name": "flyer_id", "type": "string", "facet": True},
        {"name": "retailer", "type": "string", "facet": True},
        {"name": "page_number", "type": "int32", "facet": True},
        {"name": "product_name", "type": "string"},
        {"name": "brand", "type": "string", "facet": True},
        {"name": "description", "type": "string"},
        {"name": "price_eur", "type": "float", "facet": True},
        {"name": "old_price_eur", "type": "float", "facet": True},
        {"name": "unit", "type": "string"},
        {"name": "unit_price_eur", "type": "float", "facet": True},
        {"name": "discount_text", "type": "string", "facet": True},
        {"name": "valid_from", "type": "int64", "facet": True},
        {"name": "valid_to", "type": "int64", "facet": True},
        {"name": "currency", "type": "string", "facet": True},
        {"name": "bonus_text", "type": "string"},
        {"name": "image_path", "type": "string"},
        {"name": "bbox_x1", "type": "int32"},
        {"name": "bbox_y1", "type": "int32"},
        {"name": "bbox_x2", "type": "int32"},
        {"name": "bbox_y2", "type": "int32"},
        {"name": "confidence", "type": "float"},
        {"name": "parse_error", "type": "bool", "facet": True},
        {"name": "created_at", "type": "int64", "facet": True},
    ],
    "default_sorting_field": "created_at",
}
