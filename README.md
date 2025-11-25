# Flyeralarm

Repo that makes flyers searchable

## Overview

This repository provides a Python pipeline that turns flyer images (PNG/JPG) or PDFs into searchable offer records in Typesense. It implements the stages from the requirements document:

1. **Input & Preprocessing** – render PDF pages or normalize individual images (RGB, max dimension configurable).
2. **YOLO Inference** – run a trained YOLO model to detect offer tiles/bounding boxes with configurable confidence and class filters.
3. **Cropper** – generate image crops per detected bounding box.
4. **Vision Extractor** – send each crop to an OpenAI vision model and request structured JSON.
5. **Validator & Normalizer** – coerce numeric/date fields and flag parse errors.
6. **Typesense Writer** – upsert the validated offers into a Typesense collection using the provided schema.

## Getting started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy and edit the sample configuration:
   ```bash
   cp config.sample.yaml config.yaml
   # update paths, model names, API keys
   ```

3. Run the pipeline:
   ```bash
   python -m flyeralarm.pipeline \
     --flyer-id rewe_2025_kw48 \
     --retailer rewe \
     --input /data/flyers/rewe_2025_kw48.pdf \
     --rendered-dir /data/flyers/pages \
     --crops-dir /data/flyers/crops \
     --yolo-model models/best.pt \
     --typesense-host localhost \
     --typesense-port 8108 \
     --typesense-protocol http \
     --typesense-api-key dev-key \
     --openai-key $OPENAI_API_KEY
   ```

## Module overview

- `flyeralarm.preprocessing`: accepts PDF or image input, renders/normalizes pages, and returns `PageImage` objects preserving page order.
- `flyeralarm.yolo`: wraps YOLO inference with configurable confidence and class filters, returning bounding boxes per page.
- `flyeralarm.cropping`: crops detected bounding boxes to individual files for downstream extraction.
- `flyeralarm.vision_extractor`: sends crops to OpenAI vision (Responses API) and returns structured JSON with raw responses attached.
- `flyeralarm.validation`: normalizes/validates parsed payloads and builds `OfferRecord` objects with timestamps and parse-error handling.
- `flyeralarm.typesense_writer`: contains the `offers` collection schema and a writer that batch-upserts records.
- `flyeralarm.pipeline`: orchestrates the end-to-end flow and exposes a CLI.

## Typesense schema

The Typesense schema mirrors the requirement specification and is available as `flyeralarm.typesense_writer.OFFERS_SCHEMA`:

```json
{
  "name": "offers",
  "default_sorting_field": "created_at",
  "fields": [
    { "name": "id",            "type": "string" },
    { "name": "flyer_id",      "type": "string",  "facet": true },
    { "name": "retailer",      "type": "string",  "facet": true },
    { "name": "page_number",   "type": "int32",   "facet": true },
    { "name": "product_name",  "type": "string" },
    { "name": "brand",         "type": "string",  "facet": true },
    { "name": "description",   "type": "string" },
    { "name": "price_eur",     "type": "float",   "facet": true },
    { "name": "old_price_eur", "type": "float",   "facet": true },
    { "name": "unit",          "type": "string" },
    { "name": "unit_price_eur","type": "float",   "facet": true },
    { "name": "discount_text", "type": "string",  "facet": true },
    { "name": "valid_from",    "type": "int64",   "facet": true },
    { "name": "valid_to",      "type": "int64",   "facet": true },
    { "name": "currency",      "type": "string",  "facet": true },
    { "name": "bonus_text",    "type": "string" },
    { "name": "image_path",    "type": "string" },
    { "name": "bbox_x1",       "type": "int32" },
    { "name": "bbox_y1",       "type": "int32" },
    { "name": "bbox_x2",       "type": "int32" },
    { "name": "bbox_y2",       "type": "int32" },
    { "name": "confidence",    "type": "float" },
    { "name": "parse_error",   "type": "bool",    "facet": true },
    { "name": "created_at",    "type": "int64",   "facet": true }
  ]
}
```

## Notes

- Bounding boxes are preserved in pixel coordinates relative to the original page image.
- The pipeline batches offer upserts to Typesense for efficiency and surfaces parse errors flagged by the vision model or validator.
