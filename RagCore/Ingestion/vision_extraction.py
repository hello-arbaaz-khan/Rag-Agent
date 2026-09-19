import base64
import os

import fitz  # PyMuPDF
from decouple import config
from groq import Groq

from RagCore.Ingestion.document import DocumentPage
from RagCore.ErrorsHandle.exceptions import IngestionError


class VisionExtractionEngine:

    MODEL_NAME = "llama-3.2-11b-vision-preview"
    PDF_RENDER_SCALE = 2.0

    OCR_PROMPT = (
        "You are an expert OCR and document analysis engine. "
        "Extract ALL readable text, headings, and data from this image. "
        "If you see a table, format it cleanly using GitHub-Flavored Markdown. "
        "Preserve the logical reading order. "
        "Do not add conversational filler, intro, or outro text. "
        "Return ONLY the extracted content."
    )

    @staticmethod
    def _encode_image_to_base64(file_path: str) -> str:
        """
        Read an image file and return its base64 representation.
        """
        if not os.path.exists(file_path):
            raise IngestionError(
                f"Target image file not found at: {file_path}"
            )

        try:
            with open(file_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")

        except OSError as exc:
            raise IngestionError(
                f"Failed to read image for base64 encoding: {exc}"
            ) from exc

    @staticmethod
    def _encode_image_bytes_to_base64(image_bytes: bytes) -> str:
        """
        Encode in-memory image bytes to base64.

        Used for PDF pages rendered directly in memory.
        """
        if not image_bytes:
            raise IngestionError(
                "Cannot encode empty image bytes."
            )

        return base64.b64encode(image_bytes).decode("utf-8")

    @staticmethod
    def _get_client() -> Groq:
        """
        Create and return the Groq client.
        """
        api_key = config("GROQ_API_KEY", default=None)

        if not api_key:
            raise IngestionError(
                "GROQ_API_KEY environment variable is missing "
                "from your .env configuration."
            )

        return Groq(api_key=api_key)

    @classmethod
    def _extract_base64_image_text(
        cls,
        base64_image: str,
        mime_type: str,
    ) -> str:
        """
        Send a base64-encoded image to the vision model.

        Returns an empty string when OCR finds no readable content.
        """
        if not base64_image:
            raise IngestionError(
                "Cannot perform OCR on an empty image payload."
            )

        client = cls._get_client()

        try:
            response = client.chat.completions.create(
                model=cls.MODEL_NAME,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": cls.OCR_PROMPT,
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": (
                                        f"data:{mime_type};base64,"
                                        f"{base64_image}"
                                    )
                                },
                            },
                        ],
                    }
                ],
                temperature=0.0,
                max_tokens=4096,
            )

            extracted_text = response.choices[0].message.content

            if not extracted_text:
                return ""

            return extracted_text.strip()

        except Exception as exc:
            raise IngestionError(
                f"Vision Engine failed processing image via Groq API: {exc}"
            ) from exc

    @classmethod
    def extract_image_text(cls, file_path: str) -> str:
        """
        Extract text from a single image file.
        """
        if not os.path.exists(file_path):
            raise IngestionError(
                f"Target image file not found at: {file_path}"
            )

        _, ext = os.path.splitext(file_path.lower())

        mime_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".tiff": "image/tiff",
        }

        mime_type = mime_type_map.get(ext)

        if not mime_type:
            raise IngestionError(
                f"Unsupported image format for Vision Engine: '{ext}'"
            )

        base64_image = cls._encode_image_to_base64(file_path)

        extracted_text = cls._extract_base64_image_text(
            base64_image=base64_image,
            mime_type=mime_type,
        )

        if not extracted_text or not extracted_text.strip():
            raise IngestionError(
                "Groq Vision API returned no readable text from the image."
            )

        return extracted_text

    @classmethod
    def extract_pdf_pages(
        cls,
        file_path: str,
    ) -> list[DocumentPage]:

        if not os.path.exists(file_path):
            raise IngestionError(
                f"Target PDF file not found at: {file_path}"
            )

        _, ext = os.path.splitext(file_path.lower())

        if ext != ".pdf":
            raise IngestionError(
                "extract_pdf_pages() only supports PDF files."
            )

        pages: list[DocumentPage] = []

        try:
            with fitz.open(file_path) as document:
                for page_index, page in enumerate(document):
                    page_number = page_index + 1

                    # Render the PDF page to an image in memory.
                    pixmap = page.get_pixmap(
                        matrix=fitz.Matrix(
                            cls.PDF_RENDER_SCALE,
                            cls.PDF_RENDER_SCALE,
                        ),
                        alpha=False,
                    )

                    image_bytes = pixmap.tobytes("png")

                    base64_image = cls._encode_image_bytes_to_base64(
                        image_bytes
                    )

                    extracted_text = cls._extract_base64_image_text(
                        base64_image=base64_image,
                        mime_type="image/png",
                    )

                    # Do NOT create chunks/pages for genuinely blank pages.
                    if not extracted_text:
                        continue

                    pages.append(
                        DocumentPage(
                            page_number=page_number,
                            content=extracted_text,
                        )
                    )

            if not pages:
                raise IngestionError(
                    "Vision OCR completed, but no readable content "
                    "was found on any PDF page."
                )

            return pages

        except IngestionError:
            raise

        except Exception as exc:
            raise IngestionError(
                f"Failed OCR processing scanned PDF: {exc}"
            ) from exc