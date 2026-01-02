"""
VLM Service - Vision Language Model Integration
================================================

Service for communicating with llama.cpp server running SmolVLM model
to provide contextual assistance for visually impaired users.
"""

import asyncio
import base64
import logging
import time
from typing import Dict, List, Optional, Tuple
from io import BytesIO

import httpx
from PIL import Image

from .prompt_templates import PromptTemplates

logger = logging.getLogger(__name__)


class VLMService:
    """Service for interacting with SmolVLM via llama.cpp server."""
    
    def __init__(
        self,
        server_url: str = "http://localhost:8080",
        timeout: float = 30.0,
        max_retries: int = 2
    ):
        """
        Initialize VLM service.
        
        Args:
            server_url: URL of llama.cpp server
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.server_url = server_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.prompt_templates = PromptTemplates()
        
        logger.info(f"VLM Service initialized with server: {self.server_url}")
    
    async def is_server_ready(self) -> bool:
        """
        Check if llama.cpp server is ready.
        
        Returns:
            True if server is ready, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.server_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
    
    def _encode_image_to_base64(self, image_bytes: bytes) -> str:
        """
        Encode image bytes to base64 string.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Base64 encoded string
        """
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def _prepare_image(self, image_bytes: bytes, max_size: int = 768) -> bytes:
        """
        Prepare image for VLM (resize if needed to reduce processing time).
        
        Args:
            image_bytes: Raw image bytes
            max_size: Maximum dimension (width or height)
            
        Returns:
            Processed image bytes
        """
        try:
            img = Image.open(BytesIO(image_bytes))
            
            # Resize if image is too large
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"Resized image to {new_size}")
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save to bytes with higher quality
            output = BytesIO()
            img.save(output, format='JPEG', quality=95)  # Increased from 85 to 95
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Image preparation failed: {e}")
            return image_bytes
    
    async def ask_context(
        self,
        image_bytes: bytes,
        question: str,
        detections: Optional[List[Dict]] = None,
        additional_context: Optional[str] = None
    ) -> Tuple[str, Dict]:
        """
        Ask VLM a contextual question about the image.
        
        Args:
            image_bytes: Image data
            question: Question in Turkish
            detections: YOLO detection results
            additional_context: Additional context information
            
        Returns:
            Tuple of (answer, metadata)
            
        Raises:
            Exception if request fails after retries
        """
        start_time = time.time()
        
        # Prepare image
        prepared_image = self._prepare_image(image_bytes)
        image_b64 = self._encode_image_to_base64(prepared_image)
        
        logger.info(f"Image preparation: Original={len(image_bytes)} bytes, Prepared={len(prepared_image)} bytes, Base64={len(image_b64)} bytes")
        
        # Build prompt
        prompt = self.prompt_templates.build_prompt(
            question=question,
            detections=detections,
            additional_context=additional_context
        )
        
        logger.info(f"Asking VLM: '{question}'")
        logger.debug(f"Prompt length: {len(prompt)} chars")
        
        # Prepare request payload for llama.cpp
        payload = {
            "prompt": prompt,
            "image_data": [{"data": image_b64, "id": 1}],
            "n_predict": 50,  # Shorter = more accurate
            "temperature": 0.3,  # Very low = stick to facts
            "top_p": 0.5,  # Very conservative = only top tokens
            "top_k": 20,  # Very conservative
            "stream": False,
            "cache_prompt": False  # DISABLE caching
        }
        
        # Try request with retries
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.server_url}/completion",
                        json=payload
                    )
                    response.raise_for_status()
                    
                    result = response.json()
                    answer = result.get('content', '').strip()
                    
                    # Cleanup: Remove meta-text
                    import re
                    
                    # Remove "Chain of Thought:", "CoT:", "Thinking:", etc
                    answer = re.sub(r'(chain\s+of\s+thought|cot|thinking|analysis|reason|let\s+me|explanation|step.*?by.*?step|justification).*?:', ' ', answer, flags=re.IGNORECASE)
                    
                    # Remove prefixes like "ANSWER:", "Response:", etc
                    answer = re.sub(r'^(answer|response|cevap|reply|output):\s*', '', answer, flags=re.IGNORECASE)
                    answer = re.sub(r'^answer\s*\([^)]*\):\s*', '', answer, flags=re.IGNORECASE)
                    
                    # Remove bullet points and numbering
                    answer = re.sub(r'^[\s\-\*\d\.]+', '', answer, flags=re.MULTILINE)
                    
                    # Remove newlines, keep multiple spaces reduced
                    answer = ' '.join(answer.split())
                    answer = answer.strip()
                    
                    # Take first sentence only (before . or ?)
                    sentences = re.split(r'[.!?]', answer)
                    if sentences and sentences[0].strip():
                        answer = sentences[0].strip()
                    
                    # Limit to 20 words
                    words = answer.split()[:20]
                    answer = ' '.join(words)
                    
                    # Final cleanup
                    answer = answer.strip()
                    if not answer:
                        answer = "Unable to analyze the image. Please try again."
                    
                    elapsed_time = time.time() - start_time
                    
                    metadata = {
                        'processing_time_ms': elapsed_time * 1000,
                        'server_url': self.server_url,
                        'detections_count': len(detections) if detections else 0,
                        'tokens_generated': result.get('tokens_predicted', 0),
                        'attempt': attempt + 1
                    }
                    
                    logger.info(f"VLM answered in {elapsed_time:.2f}s: {answer[:50]}...")
                    
                    return answer, metadata
                    
            except httpx.TimeoutException:
                last_exception = Exception(f"Request timed out after {self.timeout}s")
                logger.warning(f"Attempt {attempt + 1} timed out")
                
            except httpx.HTTPStatusError as e:
                last_exception = Exception(f"HTTP error: {e.response.status_code}")
                logger.error(f"Attempt {attempt + 1} failed with HTTP {e.response.status_code}")
                
            except Exception as e:
                last_exception = e
                logger.error(f"Attempt {attempt + 1} failed: {e}")
            
            # Wait before retry (exponential backoff)
            if attempt < self.max_retries:
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
        
        # All retries failed
        error_msg = f"VLM request failed after {self.max_retries + 1} attempts: {last_exception}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    def get_preset_questions(self) -> Dict[str, str]:
        """Get all preset questions."""
        return self.prompt_templates.get_all_preset_questions()


# Singleton instance
_vlm_service: Optional[VLMService] = None


def get_vlm_service(
    server_url: str = "http://localhost:8080",
    timeout: float = 30.0
) -> VLMService:
    """
    Get or create VLM service singleton.
    
    Args:
        server_url: llama.cpp server URL
        timeout: Request timeout
        
    Returns:
        VLMService instance
    """
    global _vlm_service
    
    if _vlm_service is None:
        _vlm_service = VLMService(
            server_url=server_url,
            timeout=timeout
        )
    
    return _vlm_service