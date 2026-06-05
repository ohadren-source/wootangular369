"""
ELEPHANT ENGINE — Large file processing via AWS Lambda.

For files >900KB, don't try to read them in Sol.
Hand off to Lambda. Get back a digest. Read the digest.
"""

import os
import requests
import json
import logging

logger = logging.getLogger(__name__)

LAMBDA_API_ENDPOINT = os.getenv(
    'ELEPHANT_ENGINE_ENDPOINT',
    'https://pjtwbh1i61.execute-api.us-east-1.amazonaws.com/prod/process'
)

def process_large_file(file_key: str, operations: list, bucket: str = None) -> dict:
    """
    Send a large file to Lambda for processing.

    Args:
        file_key: S3 file key (path/to/file.html)
        operations: List of operations to apply
        bucket: Optional custom bucket name (defaults to input bucket)

    Returns:
        {
            "success": True/False,
            "output_location": "s3://...",
            "download_url": "presigned URL valid for 1 hour",
            "output_size": bytes,
            "operations_applied": count
        }
    """

    payload = {
        "file_key": file_key,
        "operations": operations
    }

    if bucket:
        payload["bucket"] = bucket

    try:
        logger.info(f"[ELEPHANT] Sending {file_key} to Lambda for processing")
        response = requests.post(
            LAMBDA_API_ENDPOINT,
            json=payload,
            timeout=900  # 15 min timeout to match Lambda
        )

        response.raise_for_status()
        result = response.json()

        if result.get("success"):
            logger.info(
                f"[ELEPHANT] ✅ Processing complete: {result.get('output_size')} bytes"
            )
            return {
                "success": True,
                "download_url": result.get("download_url"),
                "output_size": result.get("output_size"),
                "operations_applied": result.get("operations_applied"),
                "output_location": result.get("output_location")
            }
        else:
            logger.error(f"[ELEPHANT] Lambda error: {result.get('error')}")
            return {
                "success": False,
                "error": result.get("error")
            }

    except requests.exceptions.Timeout:
        logger.error("[ELEPHANT] Lambda timeout (15min exceeded)")
        return {
            "success": False,
            "error": "Processing timeout — file may be too complex or large"
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"[ELEPHANT] Request failed: {e}")
        return {
            "success": False,
            "error": f"Service unavailable: {str(e)}"
        }
    except Exception as e:
        logger.error(f"[ELEPHANT] Unexpected error: {e}")
        return {
            "success": False,
            "error": f"Processing failed: {str(e)}"
        }


def process_html_file(file_key: str, operations: list) -> dict:
    """Process an HTML file via Lambda."""
    return process_large_file(file_key, operations)


def process_pdf_file(file_key: str, operations: list) -> dict:
    """Process a PDF file via Lambda."""
    return process_large_file(file_key, operations)


def process_csv_file(file_key: str, operations: list) -> dict:
    """Process a CSV file via Lambda."""
    return process_large_file(file_key, operations)


def process_image_file(file_key: str, operations: list) -> dict:
    """Process an image file via Lambda."""
    return process_large_file(file_key, operations)
