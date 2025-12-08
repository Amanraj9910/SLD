"""
PDF Processing Service for SLD Component Detection
Handles PDF file upload, page extraction, and multi-page component detection.
"""

import os
import logging
import tempfile
import asyncio
import uuid
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

import fitz  # PyMuPDF
from PIL import Image
import numpy as np

from ..annotation_tool.annotator import AnnotationManager
from web_app.core.backend.services.component_service import ComponentDetectionService
from web_app.core.backend.component_detection.predict import DetectionResult, Detection

logger = logging.getLogger(__name__)

@dataclass
class PDFPageResult:
    """Result for a single PDF page detection"""
    page_number: int
    image_path: str
    image_url: str  # URL to access the image via API
    image_dimensions: Dict[str, int]
    detections: List[Detection]
    processing_time: float
    model_info: Dict[str, Any]

@dataclass
class PDFDetectionResult:
    """Complete PDF detection result"""
    pdf_path: str
    pdf_id: str  # Unique identifier for this PDF processing session
    total_pages: int
    page_results: List[PDFPageResult]
    total_detections: int
    total_processing_time: float
    model_info: Dict[str, Any]

class PDFProcessingService:
    """Service for processing PDF files and detecting components on each page"""
    
    def __init__(self, component_service: ComponentDetectionService):
        """
        Initialize PDF processing service.

        Args:
            component_service: Component detection service instance
        """
        self.component_service = component_service
        self.temp_dir = None

        # Create persistent uploads directory for PDF images
        self.uploads_dir = Path(__file__).parent.parent / "uploads" / "pdf_images"
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
    
    def _setup_temp_directory(self) -> str:
        """Create temporary directory for PDF processing"""
        if self.temp_dir is None:
            self.temp_dir = tempfile.mkdtemp(prefix="pdf_processing_")
        return self.temp_dir
    
    def _cleanup_temp_directory(self):
        """Clean up temporary directory"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory: {e}")

    def _save_pdf_pages_persistent(self, temp_page_paths: List[str], pdf_id: str) -> List[Dict[str, str]]:
        """
        Save PDF page images to persistent storage.

        Args:
            temp_page_paths: List of temporary page image paths
            pdf_id: Unique identifier for this PDF

        Returns:
            List of dictionaries with 'path' and 'url' for each page
        """
        persistent_pages = []

        # Create directory for this PDF
        pdf_dir = self.uploads_dir / pdf_id
        pdf_dir.mkdir(exist_ok=True)

        for i, temp_path in enumerate(temp_page_paths):
            page_num = i + 1
            page_filename = f"page_{page_num:03d}.png"
            persistent_path = pdf_dir / page_filename

            # Copy from temp to persistent location
            shutil.copy2(temp_path, persistent_path)

            # Create URL for accessing the image
            image_url = f"/api/v1/pdf/{pdf_id}/page/{page_num}/image"

            persistent_pages.append({
                'path': str(persistent_path),
                'url': image_url
            })

            logger.info(f"✅ Saved page {page_num} to persistent storage: {persistent_path}")

        return persistent_pages
    
    def extract_pdf_pages(self, pdf_path: Union[str, Path], dpi: int = 300) -> List[str]:
        """
        Extract pages from PDF as images.
        
        Args:
            pdf_path: Path to PDF file
            dpi: Resolution for page extraction (default: 300 DPI for good quality)
            
        Returns:
            List of paths to extracted page images
        """
        pdf_path = str(pdf_path)
        temp_dir = self._setup_temp_directory()
        page_paths = []
        
        try:
            logger.info(f"📄 Extracting pages from PDF: {pdf_path}")
            
            # Open PDF document
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Convert page to image
                mat = fitz.Matrix(dpi/72, dpi/72)  # Scale factor for DPI
                pix = page.get_pixmap(matrix=mat)
                
                # Save as PNG
                page_filename = f"page_{page_num + 1:03d}.png"
                page_path = os.path.join(temp_dir, page_filename)
                pix.save(page_path)
                
                page_paths.append(page_path)
                logger.info(f"✅ Extracted page {page_num + 1}/{len(doc)}: {page_path}")
            
            doc.close()
            logger.info(f"📄 Successfully extracted {len(page_paths)} pages")
            
            return page_paths
            
        except Exception as e:
            logger.error(f"❌ Failed to extract PDF pages: {e}")
            raise ValueError(f"PDF extraction failed: {e}")
    
    async def detect_components_in_pdf(
        self,
        pdf_path: Union[str, Path],
        save_visualizations: bool = False,
        output_dir: Optional[str] = None
    ) -> PDFDetectionResult:
        """
        Detect components in all pages of a PDF.
        
        Args:
            pdf_path: Path to PDF file
            save_visualizations: Whether to save visualization images
            output_dir: Directory for output files
            
        Returns:
            PDFDetectionResult with detection results for all pages
        """
        pdf_path = str(pdf_path)
        start_time = asyncio.get_event_loop().time()
        
        try:
            logger.info(f"🚀 Starting PDF component detection: {pdf_path}")

            # Generate unique ID for this PDF processing session
            pdf_id = str(uuid.uuid4())
            logger.info(f"📋 PDF processing ID: {pdf_id}")

            # Extract pages from PDF
            page_paths = self.extract_pdf_pages(pdf_path)
            total_pages = len(page_paths)

            if total_pages == 0:
                raise ValueError("No pages found in PDF")

            # Save pages to persistent storage
            persistent_pages = self._save_pdf_pages_persistent(page_paths, pdf_id)
            
            # Process each page
            page_results = []
            total_detections = 0
            
            for i, page_path in enumerate(page_paths):
                page_num = i + 1
                logger.info(f"🔍 Processing page {page_num}/{total_pages}")

                try:
                    # Run component detection on this page
                    detection_result = await self.component_service.detect_components_async(
                        image_path=page_path,
                        save_visualization=save_visualizations,
                        output_dir=output_dir
                    )

                    # Get persistent page info
                    persistent_page = persistent_pages[i]

                    # Create page result
                    page_result = PDFPageResult(
                        page_number=page_num,
                        image_path=persistent_page['path'],
                        image_url=persistent_page['url'],
                        image_dimensions=detection_result.image_dimensions,
                        detections=detection_result.detections,
                        processing_time=detection_result.processing_time,
                        model_info=detection_result.model_info
                    )
                    
                    page_results.append(page_result)
                    total_detections += len(detection_result.detections)
                    
                    logger.info(f"✅ Page {page_num}: {len(detection_result.detections)} components detected")
                    
                except Exception as page_error:
                    logger.error(f"❌ Failed to process page {page_num}: {page_error}")
                    # Create empty result for failed page
                    persistent_page = persistent_pages[i]
                    page_result = PDFPageResult(
                        page_number=page_num,
                        image_path=persistent_page['path'],
                        image_url=persistent_page['url'],
                        image_dimensions={"width": 0, "height": 0},
                        detections=[],
                        processing_time=0.0,
                        model_info={}
                    )
                    page_results.append(page_result)
            
            total_processing_time = asyncio.get_event_loop().time() - start_time
            
            # Get model info from first successful page
            model_info = {}
            for page_result in page_results:
                if page_result.model_info:
                    model_info = page_result.model_info
                    break
            
            # Create final result
            pdf_result = PDFDetectionResult(
                pdf_path=pdf_path,
                pdf_id=pdf_id,
                total_pages=total_pages,
                page_results=page_results,
                total_detections=total_detections,
                total_processing_time=total_processing_time,
                model_info=model_info
            )
            
            logger.info(f"🎉 PDF processing complete: {total_detections} total components across {total_pages} pages")
            
            return pdf_result
            
        except Exception as e:
            logger.error(f"❌ PDF component detection failed: {e}")
            raise
        
        finally:
            # Cleanup temporary files
            self._cleanup_temp_directory()
    
    def get_pdf_info(self, pdf_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get basic information about a PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with PDF information
        """
        pdf_path = str(pdf_path)
        
        try:
            doc = fitz.open(pdf_path)
            
            info = {
                "total_pages": len(doc),
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "creator": doc.metadata.get("creator", ""),
                "producer": doc.metadata.get("producer", ""),
                "creation_date": doc.metadata.get("creationDate", ""),
                "modification_date": doc.metadata.get("modDate", ""),
                "file_size": os.path.getsize(pdf_path)
            }
            
            doc.close()
            return info
            
        except Exception as e:
            logger.error(f"❌ Failed to get PDF info: {e}")
            return {
                "total_pages": 0,
                "error": str(e),
                "file_size": os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0
            }
