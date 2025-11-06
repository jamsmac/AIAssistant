"""
File Processing Module for AI Chat
Handles PDF, images, and text file processing for AI analysis
"""
import base64
import io
import logging
from typing import Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# File size limits (in bytes)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_TEXT_LENGTH = 50000  # Maximum characters to extract

# Supported file types
SUPPORTED_TYPES = {
    'pdf': ['application/pdf'],
    'image': ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'],
    'text': ['text/plain', 'text/markdown', 'text/csv', 'application/json', 'text/html']
}


class FileProcessor:
    """Process uploaded files for AI analysis"""

    def __init__(self):
        self.pdf_available = False
        self.ocr_available = False
        self.vision_available = False

        # Try importing optional dependencies
        try:
            import fitz  # PyMuPDF
            self.pdf_available = True
        except ImportError:
            logger.warning("PyMuPDF not installed - PDF processing disabled")

        try:
            import pytesseract
            from PIL import Image
            self.ocr_available = True
        except ImportError:
            logger.warning("Tesseract/PIL not installed - OCR disabled")

    def validate_file(self, file_name: str, file_type: str, file_size: int) -> Tuple[bool, Optional[str]]:
        """
        Validate file before processing

        Returns: (is_valid, error_message)
        """
        # Check file size
        if file_size > MAX_FILE_SIZE:
            return False, f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024:.1f}MB"

        # Check file type
        is_supported = False
        for category, types in SUPPORTED_TYPES.items():
            if file_type in types:
                is_supported = True
                break

        if not is_supported:
            supported_list = []
            for types in SUPPORTED_TYPES.values():
                supported_list.extend(types)
            return False, f"Unsupported file type. Supported: {', '.join(supported_list)}"

        return True, None

    def process_file(self, file_name: str, file_type: str, file_content: str, use_vision: bool = True) -> Dict:
        """
        Process uploaded file and extract content for AI

        Args:
            file_name: Name of the file
            file_type: MIME type
            file_content: Base64 encoded content
            use_vision: Whether to use vision models for images

        Returns:
            Dict with 'text', 'metadata', and optionally 'image_data'
        """
        try:
            # Decode base64 content
            try:
                file_bytes = base64.b64decode(file_content)
            except Exception as e:
                logger.error(f"Failed to decode base64: {e}")
                return {
                    'text': f"[Error: Could not decode file content]",
                    'metadata': {'file_name': file_name, 'error': str(e)}
                }

            # Validate size
            file_size = len(file_bytes)
            is_valid, error = self.validate_file(file_name, file_type, file_size)
            if not is_valid:
                return {
                    'text': f"[Error: {error}]",
                    'metadata': {'file_name': file_name, 'error': error}
                }

            # Route to appropriate processor
            if file_type in SUPPORTED_TYPES['pdf']:
                return self._process_pdf(file_name, file_bytes)
            elif file_type in SUPPORTED_TYPES['image']:
                return self._process_image(file_name, file_bytes, file_type, use_vision)
            elif file_type in SUPPORTED_TYPES['text']:
                return self._process_text(file_name, file_bytes, file_type)
            else:
                return {
                    'text': f"[Unsupported file type: {file_type}]",
                    'metadata': {'file_name': file_name}
                }

        except Exception as e:
            logger.error(f"Error processing file {file_name}: {e}", exc_info=True)
            return {
                'text': f"[Error processing file: {str(e)}]",
                'metadata': {'file_name': file_name, 'error': str(e)}
            }

    def _process_pdf(self, file_name: str, file_bytes: bytes) -> Dict:
        """Extract text from PDF"""
        if not self.pdf_available:
            return {
                'text': "[PDF processing not available - PyMuPDF not installed]",
                'metadata': {'file_name': file_name, 'type': 'pdf', 'error': 'missing_dependency'}
            }

        try:
            import fitz  # PyMuPDF

            # Open PDF from bytes
            pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")

            # Extract text from all pages
            text_parts = []
            total_chars = 0

            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]
                page_text = page.get_text()

                # Check if we're approaching the limit
                if total_chars + len(page_text) > MAX_TEXT_LENGTH:
                    remaining = MAX_TEXT_LENGTH - total_chars
                    text_parts.append(f"\n--- Page {page_num + 1} (truncated) ---\n")
                    text_parts.append(page_text[:remaining])
                    text_parts.append(f"\n\n[...PDF truncated at {MAX_TEXT_LENGTH} characters...]")
                    break

                text_parts.append(f"\n--- Page {page_num + 1} ---\n")
                text_parts.append(page_text)
                total_chars += len(page_text)

            pdf_doc.close()

            extracted_text = "".join(text_parts).strip()

            if not extracted_text:
                extracted_text = "[PDF appears to be empty or contains only images]"

            return {
                'text': extracted_text,
                'metadata': {
                    'file_name': file_name,
                    'type': 'pdf',
                    'pages': len(pdf_doc),
                    'chars': total_chars,
                    'truncated': total_chars >= MAX_TEXT_LENGTH
                }
            }

        except Exception as e:
            logger.error(f"Error processing PDF: {e}", exc_info=True)
            return {
                'text': f"[Error extracting PDF text: {str(e)}]",
                'metadata': {'file_name': file_name, 'type': 'pdf', 'error': str(e)}
            }

    def _process_image(self, file_name: str, file_bytes: bytes, file_type: str, use_vision: bool) -> Dict:
        """Process image - either OCR or prepare for vision model"""
        try:
            from PIL import Image

            # Open image
            image = Image.open(io.BytesIO(file_bytes))
            width, height = image.size

            # If vision models are requested, return image data for model
            if use_vision:
                # Re-encode to base64 for vision models (OpenAI, Claude)
                image_b64 = base64.b64encode(file_bytes).decode('utf-8')

                return {
                    'text': f"[Image: {file_name} - {width}x{height}px - Ready for AI vision analysis]",
                    'metadata': {
                        'file_name': file_name,
                        'type': 'image',
                        'width': width,
                        'height': height,
                        'format': image.format
                    },
                    'image_data': {
                        'base64': image_b64,
                        'mime_type': file_type
                    }
                }

            # Otherwise, try OCR if available
            if self.ocr_available:
                try:
                    import pytesseract

                    # Perform OCR
                    ocr_text = pytesseract.image_to_string(image)

                    if ocr_text.strip():
                        text = f"[OCR Text from {file_name}]:\n\n{ocr_text}"
                    else:
                        text = f"[Image {file_name} - No text detected via OCR]"

                    return {
                        'text': text,
                        'metadata': {
                            'file_name': file_name,
                            'type': 'image',
                            'width': width,
                            'height': height,
                            'ocr_used': True
                        }
                    }
                except Exception as ocr_error:
                    logger.warning(f"OCR failed: {ocr_error}")
                    return {
                        'text': f"[Image: {file_name} - OCR failed, vision model recommended]",
                        'metadata': {
                            'file_name': file_name,
                            'type': 'image',
                            'width': width,
                            'height': height,
                            'ocr_error': str(ocr_error)
                        }
                    }
            else:
                return {
                    'text': f"[Image: {file_name} - {width}x{height}px - OCR not available, please use vision model]",
                    'metadata': {
                        'file_name': file_name,
                        'type': 'image',
                        'width': width,
                        'height': height,
                        'ocr_available': False
                    }
                }

        except Exception as e:
            logger.error(f"Error processing image: {e}", exc_info=True)
            return {
                'text': f"[Error processing image: {str(e)}]",
                'metadata': {'file_name': file_name, 'type': 'image', 'error': str(e)}
            }

    def _process_text(self, file_name: str, file_bytes: bytes, file_type: str) -> Dict:
        """Process text files"""
        try:
            # Try to decode as UTF-8
            try:
                text = file_bytes.decode('utf-8')
            except UnicodeDecodeError:
                # Try other encodings
                for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        text = file_bytes.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    return {
                        'text': "[Error: Could not decode text file - unsupported encoding]",
                        'metadata': {'file_name': file_name, 'type': 'text', 'error': 'encoding'}
                    }

            # Truncate if too long
            if len(text) > MAX_TEXT_LENGTH:
                text = text[:MAX_TEXT_LENGTH] + f"\n\n[...Text truncated at {MAX_TEXT_LENGTH} characters...]"
                truncated = True
            else:
                truncated = False

            return {
                'text': f"[Content of {file_name}]:\n\n{text}",
                'metadata': {
                    'file_name': file_name,
                    'type': 'text',
                    'mime_type': file_type,
                    'chars': len(text),
                    'truncated': truncated
                }
            }

        except Exception as e:
            logger.error(f"Error processing text file: {e}", exc_info=True)
            return {
                'text': f"[Error processing text file: {str(e)}]",
                'metadata': {'file_name': file_name, 'type': 'text', 'error': str(e)}
            }


# Global instance
file_processor = FileProcessor()


def process_uploaded_file(file_name: str, file_type: str, file_content: str, use_vision: bool = True) -> Dict:
    """
    Convenience function to process uploaded files

    Args:
        file_name: Name of the uploaded file
        file_type: MIME type
        file_content: Base64 encoded content
        use_vision: Whether to use vision models for images

    Returns:
        Dict with extracted content and metadata
    """
    return file_processor.process_file(file_name, file_type, file_content, use_vision)
