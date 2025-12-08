#!/usr/bin/env python3
"""
Text Detection Module Initialization Script
Ensures proper connectivity between the web app backend and the text_detection folder.
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_text_detection_path():
    """
    Setup the main text detection module path and verify connectivity.
    This ensures the web app backend connects to the unified text detection system.
    Works cross-platform (Windows and Linux/Azure).

    Returns:
        bool: True if setup successful, False otherwise
    """
    try:
        backend_dir = Path(__file__).parent
        
        # Try environment variable first
        text_detection_env = os.getenv('TEXT_DETECTION_PATH')
        if text_detection_env:
            text_detection_path = Path(text_detection_env)
        else:
            # Try multiple possible locations
            possible_paths = [
                # Relative to backend dir (backend/ -> project root)
                Path(__file__).parent.parent.parent.parent / "text_detection",
                # Azure App Service path
                Path("/home/site/wwwroot/text_detection"),
                # Docker path
                Path("/app/text_detection"),
                # Alternative paths
                Path(__file__).parent.parent.parent.parent.parent / "text_detection",
            ]
            
            text_detection_path = None
            for p in possible_paths:
                if p.exists():
                    text_detection_path = p
                    break
            
            if text_detection_path is None:
                logger.info("ℹ️  Text detection module not found - feature will be unavailable")
                logger.info("   This is normal if text_detection folder is not present")
                logger.info("   Set TEXT_DETECTION_PATH environment variable to enable")
                return False

        project_root = text_detection_path.parent

        logger.info("🔗 Setting up connection to main text detection module")
        logger.info(f"   Backend directory: {backend_dir}")
        logger.info(f"   Project root: {project_root}")
        logger.info(f"   Main text detection path: {text_detection_path}")

        # Verify main text_detection directory exists
        if not text_detection_path.exists():
            logger.info(f"ℹ️  Main text detection directory not found: {text_detection_path}")
            return False

        # Verify key files exist in the main module (optional check)
        required_files = [
            "document_ocr.py",
            "__init__.py",
        ]

        missing_files = []
        for file_name in required_files:
            file_path = text_detection_path / file_name
            if not file_path.exists():
                missing_files.append(file_name)

        if missing_files:
            logger.info(f"ℹ️  Missing files in text detection module: {missing_files}")
            return False

        logger.info("✅ All required files found in main text detection module")

        # Add paths to sys.path if not already present (append to avoid conflicts)
        paths_to_add = [str(project_root), str(text_detection_path)]

        for path in paths_to_add:
            if path not in sys.path:
                sys.path.append(path)  # Use append to avoid conflicts with backend modules
                logger.debug(f"Added to sys.path: {path}")

        # Test import from main module
        try:
            from text_detection.document_ocr import DocumentOCR, TextDetectionResult
            logger.info("✅ Successfully connected to main text detection module")
            return True
        except ImportError as e:
            logger.info(f"ℹ️  Could not import from main text detection module: {e}")
            return False

    except Exception as e:
        logger.info(f"ℹ️  Text detection module not available: {e}")
        return False

def verify_azure_config():
    """
    Verify Azure Document Intelligence configuration.
    
    Returns:
        bool: True if Azure is configured, False otherwise
    """
    try:
        endpoint = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
        api_key = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_KEY')
        
        if not endpoint:
            logger.warning("⚠️  AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT not set")
            return False
        
        if not api_key:
            logger.warning("⚠️  AZURE_DOCUMENT_INTELLIGENCE_KEY not set")
            return False
        
        logger.info("✅ Azure Document Intelligence credentials configured")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error checking Azure configuration: {e}")
        return False

def test_text_detection_connectivity():
    """
    Test the complete text detection connectivity.
    
    Returns:
        dict: Test results
    """
    results = {
        "path_setup": False,
        "azure_config": False,
        "import_success": False,
        "overall_status": False
    }
    
    logger.info("🔍 Testing text detection connectivity...")
    
    # Test path setup
    results["path_setup"] = setup_text_detection_path()
    
    # Test Azure configuration
    results["azure_config"] = verify_azure_config()
    
    # Test imports
    if results["path_setup"]:
        try:
            from text_detection.document_ocr import DocumentOCR
            from text_detection.interactive_viewer import InteractiveTextViewer
            from text_detection.utils import TextDetectionIntegration
            results["import_success"] = True
            logger.info("✅ All text detection imports successful")
        except ImportError as e:
            logger.error(f"❌ Import test failed: {e}")
            results["import_success"] = False
    
    # Overall status
    results["overall_status"] = all([
        results["path_setup"],
        results["import_success"]
    ])
    
    # Print summary
    logger.info("\n" + "="*50)
    logger.info("TEXT DETECTION CONNECTIVITY TEST RESULTS")
    logger.info("="*50)
    logger.info(f"Path Setup:      {'✅ PASS' if results['path_setup'] else '❌ FAIL'}")
    logger.info(f"Azure Config:    {'✅ PASS' if results['azure_config'] else '⚠️  WARNING'}")
    logger.info(f"Import Test:     {'✅ PASS' if results['import_success'] else '❌ FAIL'}")
    logger.info(f"Overall Status:  {'✅ READY' if results['overall_status'] else '❌ NOT READY'}")
    logger.info("="*50)
    
    if not results["azure_config"]:
        logger.info("\n💡 To configure Azure Document Intelligence:")
        logger.info("   Set environment variables:")
        logger.info("   - AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        logger.info("   - AZURE_DOCUMENT_INTELLIGENCE_KEY")
    
    return results

if __name__ == "__main__":
    # Run connectivity test
    test_results = test_text_detection_connectivity()
    
    # Exit with appropriate code
    sys.exit(0 if test_results["overall_status"] else 1)
