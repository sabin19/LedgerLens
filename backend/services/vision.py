import os
import time
from fastapi import HTTPException
from openai import OpenAI, RateLimitError
from backend.schemas import InvoiceSchema

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "4")),
)

def call_openai_with_backoff(api_func, *args, max_retries=5, initial_delay=2, **kwargs):
    """Executes an OpenAI API method using an exponential backoff loop for 429s."""
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            return api_func(*args, **kwargs)
        except RateLimitError as error:
            if attempt == max_retries - 1:
                raise HTTPException(
                    status_code=429,
                    detail="The OpenAI API rate limit was reached. Wait a moment and retry.",
                    headers={"Retry-After": str(int(delay))},
                ) from error
            time.sleep(delay)
            delay *= 2
        except Exception as e:
            raise e

def moderate_image(data_uri: str):
    """Runs the image through OpenAI's moderation gate."""
    return call_openai_with_backoff(
        client.moderations.create,
        model="omni-moderation-latest",
        input=[{"type": "image_url", "image_url": {"url": data_uri}}]
    )

def extract_invoice_data(data_uri: str):
    """Extracts structured data using the vision model."""
    return call_openai_with_backoff(
        client.chat.completions.parse,
        model=os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini"),
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract the structured data from this invoice/receipt."},
                    {"type": "image_url", "image_url": {"url": data_uri}}
                ]
            }
        ],
        response_format=InvoiceSchema
    )