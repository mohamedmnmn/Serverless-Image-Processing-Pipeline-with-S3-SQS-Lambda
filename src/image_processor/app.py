"""Example Lambda image processor.

Production deployment should provide Pillow through a Lambda Layer or
container image built for the Lambda runtime/architecture.
"""

import io
import os
from typing import Any

import boto3
from PIL import Image, ImageDraw

s3 = boto3.client("s3")

DESTINATION_BUCKET = os.environ["DESTINATION_BUCKET"]
WATERMARK_TEXT = os.environ.get("WATERMARK_TEXT", "AWS Image Pipeline")


def download_image(bucket: str, key: str) -> Image.Image:
    response = s3.get_object(Bucket=bucket, Key=key)
    return Image.open(io.BytesIO(response["Body"].read())).convert("RGB")


def resize_image(image: Image.Image, max_size: tuple[int, int]) -> Image.Image:
    result = image.copy()
    result.thumbnail(max_size, Image.Resampling.LANCZOS)
    return result


def add_watermark(image: Image.Image) -> Image.Image:
    result = image.copy()
    draw = ImageDraw.Draw(result)
    margin = 16
    bbox = draw.textbbox((0, 0), WATERMARK_TEXT)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    x = max(margin, result.width - width - margin)
    y = max(margin, result.height - height - margin)
    draw.text((x, y), WATERMARK_TEXT, fill=(255, 255, 255))
    return result


def upload_image(image: Image.Image, key: str) -> None:
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90, optimize=True)
    buffer.seek(0)

    s3.put_object(
        Bucket=DESTINATION_BUCKET,
        Key=key,
        Body=buffer.getvalue(),
        ContentType="image/jpeg",
    )


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Process one image described by Step Functions.

    Expected event:
    {
        "sourceBucket": "...",
        "sourceKey": "...",
        "imageId": "..."
    }
    """
    source_bucket = event["sourceBucket"]
    source_key = event["sourceKey"]
    image_id = event["imageId"]

    image = download_image(source_bucket, source_key)

    full = add_watermark(resize_image(image, (2400, 2400)))
    thumbnail = add_watermark(resize_image(image, (400, 400)))

    full_key = f"processed/{image_id}/full.jpg"
    thumbnail_key = f"processed/{image_id}/thumbnail.jpg"

    upload_image(full, full_key)
    upload_image(thumbnail, thumbnail_key)

    return {
        "imageId": image_id,
        "sourceKey": source_key,
        "fullImageKey": full_key,
        "thumbnailKey": thumbnail_key,
        "width": image.width,
        "height": image.height,
    }
