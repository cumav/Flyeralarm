from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List

from PIL import Image
from pdf2image import convert_from_path

from .models import PageImage


logger = logging.getLogger(__name__)


SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def _normalize_image(image: Image.Image, max_dimension: int) -> Image.Image:
    width, height = image.size
    if max(width, height) <= max_dimension:
        return image
    scale = max_dimension / float(max(width, height))
    new_size = (int(width * scale), int(height * scale))
    logger.info("Resizing image from %s to %s", (width, height), new_size)
    return image.resize(new_size, Image.LANCZOS)


def _render_pdf(input_path: Path, output_dir: Path, flyer_id: str, max_dimension: int) -> List[PageImage]:
    logger.info("Rendering PDF %s", input_path)
    pages = convert_from_path(str(input_path))
    page_images: List[PageImage] = []
    for idx, page in enumerate(pages, start=1):
        page = _normalize_image(page.convert("RGB"), max_dimension)
        page_path = output_dir / f"{flyer_id}_page_{idx:02d}.png"
        page.save(page_path, format="PNG")
        page_images.append(PageImage(flyer_id=flyer_id, page_number=idx, image_path=str(page_path)))
    return page_images


def _handle_image(input_path: Path, output_dir: Path, flyer_id: str, max_dimension: int) -> List[PageImage]:
    logger.info("Normalizing flyer image %s", input_path)
    image = Image.open(input_path).convert("RGB")
    normalized = _normalize_image(image, max_dimension)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{flyer_id}_page_01{input_path.suffix.lower()}"
    normalized.save(output_path)
    return [PageImage(flyer_id=flyer_id, page_number=1, image_path=str(output_path))]


def preprocess_flyer(
    flyer_id: str,
    input_path: str,
    rendered_pages_dir: str,
    max_dimension: int,
) -> List[PageImage]:
    """Preprocess a flyer input and emit normalized page images."""

    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    output_dir = Path(rendered_pages_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _render_pdf(path, output_dir, flyer_id, max_dimension)
    if suffix in SUPPORTED_IMAGE_EXTENSIONS:
        return _handle_image(path, output_dir, flyer_id, max_dimension)

    raise ValueError(
        f"Unsupported input type {suffix}; supported types: PDF, {', '.join(sorted(SUPPORTED_IMAGE_EXTENSIONS))}"
    )


def collect_page_images(directory: str) -> Iterable[PageImage]:
    for file in sorted(Path(directory).glob("*")):
        if file.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
            flyer_id = file.stem.rsplit("_page_", 1)[0]
            page_number = int(file.stem.split("_page_")[-1]) if "_page_" in file.stem else 1
            yield PageImage(flyer_id=flyer_id, page_number=page_number, image_path=str(file))
