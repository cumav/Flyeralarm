from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from .models import Detection, PageImage


logger = logging.getLogger(__name__)


class YoloDetector:
    def __init__(self, model_path: str, confidence_threshold: float = 0.5, class_filter: Optional[List[str]] = None):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.class_filter = set(class_filter) if class_filter else None
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return self._model
        from ultralytics import YOLO

        model_file = Path(self.model_path)
        if not model_file.exists():
            raise FileNotFoundError(f"YOLO model file not found: {self.model_path}")
        self._model = YOLO(model_file)
        return self._model

    def detect(self, page: PageImage) -> List[Detection]:
        model = self._load_model()
        logger.info("Running YOLO on %s", page.image_path)
        results = model(page.image_path, verbose=False)
        detections: List[Detection] = []
        for idx, result in enumerate(results[0].boxes):
            conf = float(result.conf)
            cls_name = model.names[int(result.cls)]
            if conf < self.confidence_threshold:
                continue
            if self.class_filter and cls_name not in self.class_filter:
                continue
            bbox = result.xyxy[0].tolist()
            detections.append(
                Detection(
                    bbox_id=f"{page.flyer_id}_{page.page_number:02d}_{idx:04d}",
                    x1=int(bbox[0]),
                    y1=int(bbox[1]),
                    x2=int(bbox[2]),
                    y2=int(bbox[3]),
                    confidence=conf,
                    class_name=cls_name,
                )
            )
        logger.info("Detected %s bounding boxes for page %s", len(detections), page.page_number)
        return detections
