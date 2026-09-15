import os
from django import conf
from groq import Groq
import base64
from decouple import config
from RagCore.Ingestion.exceptions import IngestionError
from pygments.lexer import default
from requests import api

class VisionExtractionEngine:
    def _encode_image_to_base64(self, file_path: str) -> str:

        try:
            with open(file_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as exc:
            raise IngestionError(
                f"Fail to read image bytes for base64 encoding: {str(exc)}"
            )
    @classmethod
    def extract_image_text(cls, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise IngestionError(f"Target image file not found at: {file_path}")

        # 1. Initialize the Groq Client safely using python-decouple settings
        # (Make sure GROQ_API_KEY is defined inside your root .env file)
        api_key = config("GROQ_API_KEY", default=None)
        if not api_key:
            raise IngestionError("GROQ_API_KEY environment variable is missing from your .env configuration.")
            
        client = Groq(api_key=api_key)

        try:
            # 2. Convert the image file to a base64 payload string
            base64_image = cls._encode_image_to_base64(file_path)
            
            # Determine the correct media sub-type dynamically
            _, ext = os.path.splitext(file_path.lower())
            mime_type = f"image/{ext.replace('.', '')}"
            if ext == '.jpg':
                mime_type = "image/jpeg"

            # 3. Call Groq's blindingly fast vision model endpoint
            response = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "You are an expert OCR and document analysis engine. "
                                    "Extract ALL readable text, headings, and data from this image. "
                                    "If you see a table, format it cleanly using GitHub-Flavored Markdown grids. "
                                    "Do not add any conversational filler, intro, or outro text. Return ONLY the raw extracted content."
                                )
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.0,
                max_tokens=4096
            )

            extracted_text = response.choices[0].message.content
            
            if not extracted_text or not extracted_text.strip():
                raise IngestionError("Groq Vision API returned a completely blank text response.")

            return extracted_text.strip()

        except Exception as exc:
            if isinstance(exc, IngestionError):
                raise exc
            raise IngestionError(
                f"Vision Engine failed processing file via Groq API: {str(exc)}"
            ) from exc