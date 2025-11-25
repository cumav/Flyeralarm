from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PageImage:
    flyer_id: str
    page_number: int
    image_path: str


@dataclass
class Detection:
    bbox_id: str
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float
    class_name: str


@dataclass
class CropResult:
    flyer_id: str
    page_number: int
    bbox_id: str
    crop_path: str
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float
    class_name: str


@dataclass
class OfferRecord:
    id: str
    flyer_id: str
    retailer: str
    page_number: int
    product_name: str
    brand: Optional[str]
    description: Optional[str]
    price_eur: Optional[float]
    old_price_eur: Optional[float]
    unit: Optional[str]
    unit_price_eur: Optional[float]
    discount_text: Optional[str]
    valid_from: Optional[int]
    valid_to: Optional[int]
    currency: str
    bonus_text: Optional[str]
    image_path: str
    bbox_x1: int
    bbox_y1: int
    bbox_x2: int
    bbox_y2: int
    confidence: float
    parse_error: bool
    created_at: int
    raw_response: Optional[str] = None

    @classmethod
    def from_detection(
        cls,
        detection: Detection,
        crop_path: str,
        flyer_id: str,
        retailer: str,
        page_number: int,
        created_at: int,
        parsed: dict,
    ) -> "OfferRecord":
        return cls(
            id=parsed.get("id", detection.bbox_id),
            flyer_id=flyer_id,
            retailer=retailer,
            page_number=page_number,
            product_name=parsed.get("product_name", ""),
            brand=parsed.get("brand"),
            description=parsed.get("description"),
            price_eur=cls._to_float(parsed.get("price_eur")),
            old_price_eur=cls._to_float(parsed.get("old_price_eur")),
            unit=parsed.get("unit"),
            unit_price_eur=cls._to_float(parsed.get("unit_price_eur")),
            discount_text=parsed.get("discount_text"),
            valid_from=cls._to_int(parsed.get("valid_from")),
            valid_to=cls._to_int(parsed.get("valid_to")),
            currency=parsed.get("currency", "EUR"),
            bonus_text=parsed.get("bonus_text"),
            image_path=crop_path,
            bbox_x1=detection.x1,
            bbox_y1=detection.y1,
            bbox_x2=detection.x2,
            bbox_y2=detection.y2,
            confidence=float(detection.confidence),
            parse_error=bool(parsed.get("parse_error", False)),
            created_at=int(created_at),
            raw_response=parsed.get("raw_response"),
        )

    @staticmethod
    def _to_float(value: Optional[object]) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_int(value: Optional[object]) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None


OfferBatch = List[OfferRecord]
