from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Mapping, Optional


@dataclass
class PathsConfig:
    input_path: str
    rendered_pages_dir: str
    crops_dir: str


@dataclass
class YoloConfig:
    model_path: str
    confidence_threshold: float = 0.5
    class_filter: Optional[List[str]] = None


@dataclass
class OpenAIConfig:
    api_key: str
    model: str = "gpt-5.1-mini"
    max_output_tokens: int = 1024


@dataclass
class TypesenseConfig:
    host: str
    port: str
    protocol: str = "https"
    api_key: str = ""
    collection: str = "offers"
    batch_size: int = 40


@dataclass
class PipelineConfig:
    flyer_id: str
    retailer: str
    paths: PathsConfig
    yolo: YoloConfig
    openai: OpenAIConfig
    typesense: TypesenseConfig
    max_dimension: int = 3000
    created_at: Optional[int] = None
    crop_image_format: str = "png"
    logging_level: str = "INFO"
    metrics: List[str] = field(default_factory=lambda: [
        "pages_processed",
        "detections",
        "parse_errors",
    ])

    @classmethod
    def from_mapping(cls, data: Mapping) -> "PipelineConfig":
        return cls(
            flyer_id=data["flyer_id"],
            retailer=data["retailer"],
            paths=PathsConfig(**data["paths"]),
            yolo=YoloConfig(**data["yolo"]),
            openai=OpenAIConfig(**data["openai"]),
            typesense=TypesenseConfig(**data["typesense"]),
            max_dimension=data.get("max_dimension", 3000),
            created_at=data.get("created_at"),
            crop_image_format=data.get("crop_image_format", "png"),
            logging_level=data.get("logging_level", "INFO"),
            metrics=data.get("metrics", ["pages_processed", "detections", "parse_errors"]),
        )
