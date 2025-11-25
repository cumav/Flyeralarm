from __future__ import annotations

import base64
import json
import logging
from pathlib import Path
from typing import Dict

from openai import OpenAI

from .config import OpenAIConfig
from .models import CropResult


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are an assistant that extracts structured offer data from flyer tiles.
Return a compact JSON object with the keys:
- id (string)
- product_name (string)
- brand (string|null)
- description (string|null)
- price_eur (float|null)
- old_price_eur (float|null)
- unit (string|null)
- unit_price_eur (float|null)
- discount_text (string|null)
- valid_from (unix timestamp|null)
- valid_to (unix timestamp|null)
- currency (string, default EUR)
- bonus_text (string|null)
- parse_error (bool)
Include the raw numeric values where possible and set parse_error=true if anything looks inconsistent.
"""


def _encode_image(image_path: str) -> str:
    data = Path(image_path).read_bytes()
    return base64.b64encode(data).decode("utf-8")


def extract_offer_data(client: OpenAI, config: OpenAIConfig, crop: CropResult) -> Dict:
    image_base64 = _encode_image(crop.crop_path)
    logger.debug("Sending crop %s to OpenAI vision", crop.crop_path)
    response = client.responses.create(
        model=config.model,
        max_output_tokens=config.max_output_tokens,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract one JSON object with the described keys."},
                    {"type": "input_image", "image_url": f"data:image/png;base64,{image_base64}"},
                ],
            },
        ],
        response_format={"type": "json_object"},
    )

    content = response.output[0].content[0].text  # type: ignore[attr-defined]
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        logger.exception("Failed to parse JSON from model response")
        parsed = {"parse_error": True, "raw_response": content}
    else:
        parsed["raw_response"] = content
    return parsed


def build_openai_client(config: OpenAIConfig) -> OpenAI:
    return OpenAI(api_key=config.api_key)
