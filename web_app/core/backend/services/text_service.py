"""
Text Detection Service
Wraps the text detection module for use in the web API.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Union, List
import sys
import os

# Setup logging first
logger = logging.getLogger(__name__)

def _setup_text_detection_import():
    """
    Setup text detection module import with robust path handling.
    This function ensures the main text detection module is properly imported.
    Works cross-platform (Windows and Linux/Azure).
    """
    # Try environment variable first
    text_detection_env = os.getenv('TEXT_DETECTION_PATH')
    if text_detection_env:
        text_detection_path = Path(text_detection_env)
    else:
        # Try multiple possible locations
        possible_paths = [
            # Relative to this file (backend/services/ -> project root)
            Path(__file__).parent.parent.parent.parent.parent / "text_detection",
            # Azure App Service path
            Path("/home/site/wwwroot/text_detection"),
            # Alternative project structure
            Path(__file__).parent.parent.parent.parent.parent.parent / "text_detection",
        ]
        
        text_detection_path = None
        for p in possible_paths:
            if p.exists():
                text_detection_path = p
                logger.info(f"Found text_detection module at: {p}")
                break
        
        if text_detection_path is None:
            # Text detection module is optional - log warning but don't fail
            logger.warning(
                "Text detection module not found. Text detection features will be unavailable. "
                "Set TEXT_DETECTION_PATH environment variable to enable."
            )
            # Return mock classes to prevent import failure
            class MockDocumentOCR:
                def __init__(self, **kwargs):
                    raise RuntimeError("Text detection module not available")
            
            class MockTextDetectionResult:
                pass
            
            return MockDocumentOCR, MockTextDetectionResult

    project_root = text_detection_path.parent

    # Add paths to sys.path if not already present (append to avoid conflicts)
    paths_to_add = [str(project_root), str(text_detection_path)]
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.append(path)
            logger.debug(f"Added to sys.path: {path}")

    # Import the required classes
    try:
        from text_detection.document_ocr import DocumentOCR, TextDetectionResult
        logger.info("✅ Successfully imported from main text detection module")
        return DocumentOCR, TextDetectionResult
    except ImportError as e:
        logger.error(f"❌ Failed to import from main text detection module: {e}")
        # Try fallback direct import
        try:
            from document_ocr import DocumentOCR, TextDetectionResult
            logger.info("✅ Successfully imported using direct import fallback")
            return DocumentOCR, TextDetectionResult
        except ImportError as e2:
            logger.warning(f"Text detection import failed: {e2}. Feature will be unavailable.")
            # Return mock classes
            class MockDocumentOCR:
                def __init__(self, **kwargs):
                    raise RuntimeError("Text detection module not available")
            
            class MockTextDetectionResult:
                pass
            
            return MockDocumentOCR, MockTextDetectionResult

# Import the text detection classes
DocumentOCR, TextDetectionResult = _setup_text_detection_import()


try:
    from web_app.core.backend.utils.logging_config import log_performance
except ImportError:
    # Simple fallback decorator if logging_config is not available
    def log_performance(operation_name: str):
        def decorator(func):
            return func
        return decorator

class TextDetectionService:
    """
    Service wrapper for text detection functionality.
    Provides async interface and additional features for web API.
    """
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        model_id: str = "prebuilt-read"
    ):
        """
        Initialize the text detection service.
        
        Args:
            endpoint: Azure Document Intelligence endpoint
            api_key: Azure Document Intelligence API key
            model_id: Model ID for document analysis
        """
        self.endpoint = endpoint
        self.api_key = api_key
        self.model_id = model_id
        
        # Initialize OCR client
        self._ocr_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Azure Document Intelligence client"""
        try:
            if not self.endpoint or not self.api_key:
                logger.warning("Azure Document Intelligence credentials not provided")
                return
            
            self._ocr_client = DocumentOCR(
                endpoint=self.endpoint,
                api_key=self.api_key,
                model_id=self.model_id
            )
            logger.info("Text detection client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize text detection client: {e}")
            raise
    
    @property
    def client(self):
        """Get the underlying OCR client"""
        return self._ocr_client
    
    @log_performance("Text Detection")
    async def extract_text_async(
        self,
        document_path: Union[str, Path],
        output_format: str = "detailed",
        save_results: bool = False,
        output_dir: Optional[str] = None
    ) -> TextDetectionResult:
        """
        Async wrapper for text extraction.

        Args:
            document_path: Path to input document
            output_format: Output format (detailed or simple)
            save_results: Whether to save results to JSON file
            output_dir: Directory to save results (optional)

        Returns:
            TextDetectionResult object
        """
        if not self._ocr_client:
            raise RuntimeError("Text detection client not initialized")
        
        # Run extraction in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self._ocr_client.extract_text,
            document_path,
            output_format,
            save_results,
            output_dir
        )
        
        return result
    
    def extract_text_sync(
        self,
        document_path: Union[str, Path],
        output_format: str = "detailed",
        save_results: bool = False,
        output_dir: Optional[str] = None
    ) -> TextDetectionResult:
        """
        Synchronous text extraction.

        Args:
            document_path: Path to input document
            output_format: Output format (detailed or simple)
            save_results: Whether to save results to JSON file
            output_dir: Directory to save results (optional)

        Returns:
            TextDetectionResult object
        """
        if not self._ocr_client:
            raise RuntimeError("Text detection client not initialized")
        
        return self._ocr_client.extract_text(
            document_path=document_path,
            output_format=output_format,
            save_results=save_results,
            output_dir=output_dir
        )
    
    async def extract_batch_async(
        self,
        document_paths: List[Union[str, Path]],
        output_dir: Optional[str] = None
    ) -> List[TextDetectionResult]:
        """
        Async batch text extraction.
        
        Args:
            document_paths: List of document paths
            output_dir: Directory to save individual results
            
        Returns:
            List of TextDetectionResult objects
        """
        if not self._ocr_client:
            raise RuntimeError("Text detection client not initialized")
        
        # Run batch extraction in thread pool
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            self._ocr_client.extract_text_batch,
            document_paths,
            output_dir
        )
        
        return results
    
    def export_results(
        self,
        result: TextDetectionResult,
        output_path: Union[str, Path],
        format: str = "json"
    ):
        """
        Export text detection results.
        
        Args:
            result: TextDetectionResult object
            output_path: Path to save results
            format: Export format (json, txt, csv)
        """
        if not self._ocr_client:
            raise RuntimeError("Text detection client not initialized")
        
        self._ocr_client.export_result(result, output_path, format)
    
    async def test_connection_async(self) -> bool:
        """
        Test connection to Azure Document Intelligence service.
        
        Returns:
            True if connection is successful
        """
        if not self._ocr_client:
            return False
        
        try:
            # Run connection test in thread pool
            loop = asyncio.get_event_loop()
            
            # Create a simple test using the config module
            from text_detection.config.azure_config import ConfigManager
            
            config = ConfigManager.load_config(
                endpoint=self.endpoint,
                api_key=self.api_key,
                model_id=self.model_id
            )
            
            result = await loop.run_in_executor(
                None,
                ConfigManager.test_connection,
                config
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def test_connection_sync(self) -> bool:
        """
        Synchronous connection test.
        
        Returns:
            True if connection is successful
        """
        if not self._ocr_client:
            return False
        
        try:
            from text_detection.config.azure_config import ConfigManager
            
            config = ConfigManager.load_config(
                endpoint=self.endpoint,
                api_key=self.api_key,
                model_id=self.model_id
            )
            
            return ConfigManager.test_connection(config)
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_service_info(self) -> dict:
        """Get information about the text detection service"""
        return {
            "service": "Azure Document Intelligence",
            "endpoint": self.endpoint,
            "model_id": self.model_id,
            "api_version": "2024-02-29-preview",
            "configured": bool(self.endpoint and self.api_key),
            "supported_formats": self.get_supported_formats()
        }
    
    def get_supported_formats(self) -> dict:
        """Get list of supported document formats"""
        return {
            "image_formats": [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"],
            "document_formats": [".pdf"],
            "max_file_size": "500MB",
            "languages_supported": "100+ languages"
        }
    
    def validate_document(self, document_path: Union[str, Path]) -> bool:
        """
        Validate if document can be processed.
        
        Args:
            document_path: Path to document file
            
        Returns:
            True if document is valid
        """
        try:
            document_path = Path(document_path)
            
            if not document_path.exists():
                return False
            
            # Check file extension
            supported_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".pdf"]
            if document_path.suffix.lower() not in supported_extensions:
                return False
            
            # Check file size (500MB limit for Azure)
            max_size = 500 * 1024 * 1024  # 500MB
            if document_path.stat().st_size > max_size:
                return False
            
            return True
            
        except Exception:
            return False
    
    def update_credentials(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        model_id: Optional[str] = None
    ):
        """
        Update Azure credentials and reinitialize client.
        
        Args:
            endpoint: New Azure endpoint
            api_key: New Azure API key
            model_id: New model ID
        """
        if endpoint is not None:
            self.endpoint = endpoint
        
        if api_key is not None:
            self.api_key = api_key
        
        if model_id is not None:
            self.model_id = model_id
        
        # Reinitialize client with new credentials
        self._initialize_client()
        logger.info("Text detection service credentials updated")
    
    def get_usage_statistics(self) -> dict:
        """Get usage statistics (placeholder for future implementation)"""
        return {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_processing_time": 0.0,
            "total_text_extracted": 0
        }
    
    def cleanup(self):
        """Cleanup resources"""
        if self._ocr_client:
            # Clear client from memory if needed
            self._ocr_client = None
        logger.info("Text detection service cleaned up")

# Singleton instance for the application
_text_service_instance = None

def get_text_service_instance(**kwargs) -> TextDetectionService:
    """Get singleton instance of text detection service"""
    global _text_service_instance
    
    if _text_service_instance is None:
        _text_service_instance = TextDetectionService(**kwargs)
    
    return _text_service_instance
