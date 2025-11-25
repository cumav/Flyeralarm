from __future__ import annotations

import argparse
import logging
from typing import List

from .config import OpenAIConfig, PathsConfig, PipelineConfig, TypesenseConfig, YoloConfig
from .cropping import crop_detections
from .preprocessing import preprocess_flyer
from .validation import build_offer_record, timestamp_or_now
from .vision_extractor import build_openai_client, extract_offer_data
from .yolo import YoloDetector
from .typesense_writer import TypesenseWriter, OFFERS_SCHEMA


logger = logging.getLogger(__name__)


def run_pipeline(config: PipelineConfig) -> List[str]:
    logging.basicConfig(level=getattr(logging, config.logging_level.upper(), logging.INFO))
    logger.info("Starting pipeline for flyer %s", config.flyer_id)
    created_at = timestamp_or_now(config.created_at)

    pages = preprocess_flyer(
        flyer_id=config.flyer_id,
        input_path=config.paths.input_path,
        rendered_pages_dir=config.paths.rendered_pages_dir,
        max_dimension=config.max_dimension,
    )

    detector = YoloDetector(
        model_path=config.yolo.model_path,
        confidence_threshold=config.yolo.confidence_threshold,
        class_filter=config.yolo.class_filter,
    )
    client = build_openai_client(config.openai)
    writer = TypesenseWriter(config.typesense)
    writer.ensure_schema(OFFERS_SCHEMA)

    batch_records = []
    crop_paths: List[str] = []

    for page in pages:
        detections = detector.detect(page)
        crops = crop_detections(
            page=page,
            detections=detections,
            output_dir=config.paths.crops_dir,
            image_format=config.crop_image_format,
        )
        for crop, detection in zip(crops, detections):
            parsed = extract_offer_data(client, config.openai, crop)
            record = build_offer_record(
                crop=crop,
                detection=detection,
                flyer_id=config.flyer_id,
                retailer=config.retailer,
                created_at=created_at,
                payload=parsed,
            )
            batch_records.append(record)
            crop_paths.append(crop.crop_path)

    writer.upsert_batch(batch_records)
    logger.info("Completed pipeline with %s offers", len(batch_records))
    return crop_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process flyer images into Typesense offers")
    parser.add_argument("--flyer-id", required=True)
    parser.add_argument("--retailer", required=True)
    parser.add_argument("--input", dest="input_path", required=True)
    parser.add_argument("--rendered-dir", required=True)
    parser.add_argument("--crops-dir", required=True)
    parser.add_argument("--yolo-model", required=True)
    parser.add_argument("--typesense-host", required=True)
    parser.add_argument("--typesense-port", required=True)
    parser.add_argument("--typesense-protocol", default="https")
    parser.add_argument("--typesense-api-key", required=True)
    parser.add_argument("--openai-key", required=True)
    parser.add_argument("--openai-model", default="gpt-5.1-mini")
    parser.add_argument("--confidence", type=float, default=0.5)
    parser.add_argument("--max-dimension", type=int, default=3000)
    parser.add_argument("--crop-format", default="png")
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--created-at", type=int, default=None)
    return parser.parse_args()


def main():
    args = parse_args()
    config = PipelineConfig(
        flyer_id=args.flyer_id,
        retailer=args.retailer,
        paths=PathsConfig(
            input_path=args.input_path,
            rendered_pages_dir=args.rendered_dir,
            crops_dir=args.crops_dir,
        ),
        yolo=YoloConfig(
            model_path=args.yolo_model,
            confidence_threshold=args.confidence,
        ),
        openai=OpenAIConfig(
            api_key=args.openai_key,
            model=args.openai_model,
        ),
        typesense=TypesenseConfig(
            host=args.typesense_host,
            port=args.typesense_port,
            protocol=args.typesense_protocol,
            api_key=args.typesense_api_key,
        ),
        max_dimension=args.max_dimension,
        crop_image_format=args.crop_format,
        logging_level=args.log_level,
        created_at=args.created_at,
    )
    run_pipeline(config)


if __name__ == "__main__":
    main()
