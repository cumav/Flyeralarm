from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict

from .models import CropResult, Detection, OfferRecord


logger = logging.getLogger(__name__)


def normalize_offer_payload(payload: Dict) -> Dict:
    normalized = dict(payload)
    normalized.setdefault("product_name", "")
    normalized.setdefault("currency", "EUR")
    normalized.setdefault("parse_error", False)
    for key in ["price_eur", "old_price_eur", "unit_price_eur"]:
        value = normalized.get(key)
        try:
            normalized[key] = float(value) if value is not None else None
        except (TypeError, ValueError):
            normalized[key] = None
            normalized["parse_error"] = True
    for key in ["valid_from", "valid_to"]:
        value = normalized.get(key)
        try:
            normalized[key] = int(value) if value is not None else None
        except (TypeError, ValueError):
            normalized[key] = None
            normalized["parse_error"] = True
    return normalized


def build_offer_record(
    crop: CropResult,
    detection: Detection,
    flyer_id: str,
    retailer: str,
    created_at: int,
    payload: Dict,
) -> OfferRecord:
    normalized = normalize_offer_payload(payload)
    if not normalized.get("product_name"):
        normalized["parse_error"] = True
    record = OfferRecord.from_detection(
        detection=detection,
        crop_path=crop.crop_path,
        flyer_id=flyer_id,
        retailer=retailer,
        page_number=crop.page_number,
        created_at=created_at,
        parsed=normalized,
    )
    logger.debug("Built offer record %s", record.id)
    return record


def timestamp_or_now(value: int | None) -> int:
    return value if value is not None else int(datetime.utcnow().timestamp())
