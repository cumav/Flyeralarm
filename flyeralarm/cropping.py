from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from PIL import Image

from .models import CropResult, Detection, PageImage


logger = logging.getLogger(__name__)


def crop_detections(
    page: PageImage,
    detections: List[Detection],
    output_dir: str,
    image_format: str = "png",
) -> List[CropResult]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    with Image.open(page.image_path) as image:
        results: List[CropResult] = []
        for detection in detections:
            box = (detection.x1, detection.y1, detection.x2, detection.y2)
            crop = image.crop(box)
            crop_name = f"{detection.bbox_id}.{image_format}"
            crop_file = output_path / crop_name
            crop.save(crop_file, format=image_format.upper())
            results.append(
                CropResult(
                    flyer_id=page.flyer_id,
                    page_number=page.page_number,
                    bbox_id=detection.bbox_id,
                    crop_path=str(crop_file),
                    x1=detection.x1,
                    y1=detection.y1,
                    x2=detection.x2,
                    y2=detection.y2,
                    confidence=detection.confidence,
                    class_name=detection.class_name,
                )
            )
            logger.debug("Created crop %s", crop_file)
    logger.info("Created %s crops for page %s", len(results), page.page_number)
    return results
