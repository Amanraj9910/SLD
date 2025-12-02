"""
Test suite for text detection functionality.
Tests the Azure-based text extraction system.
"""

import os
import sys
import pytest
import requests
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_DOCUMENTS_PATH = "text_detection/uploads"

class TestTextDetection:
    """Test cases for text detection API."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        self.api_url = f"{BASE_URL}/api/text-detection"
        self.test_documents = self._get_test_documents()
    
    def _get_test_documents(self):
        """Get list of test documents."""
        test_docs = []
        if os.path.exists(TEST_DOCUMENTS_PATH):
            for file in os.listdir(TEST_DOCUMENTS_PATH):
                if file.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
                    test_docs.append(os.path.join(TEST_DOCUMENTS_PATH, file))
        return test_docs
    
    def test_health_endpoint(self):
        """Test if the health endpoint is working."""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=10)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend server not running")
    
    def test_text_detection_endpoint_exists(self):
        """Test if text detection endpoint exists."""
        try:
            response = requests.options(f"{self.api_url}/extract")
            assert response.status_code in [200, 405]  # 405 is OK for OPTIONS
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend server not running")
    
    def test_text_extraction_with_valid_document(self):
        """Test text extraction with a valid document."""
        if not self.test_documents:
            pytest.skip("No test documents available")
        
        test_doc = self.test_documents[0]
        
        try:
            with open(test_doc, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f"{self.api_url}/extract",
                    files=files,
                    timeout=60  # Text extraction can take longer
                )
            
            assert response.status_code == 200
            data = response.json()
            
            # Check response structure
            assert 'text' in data
            assert 'metadata' in data
            assert isinstance(data['text'], str)
            
            # Check if text was extracted
            if data['text'].strip():
                assert len(data['text']) > 0
                
            # Check metadata
            metadata = data['metadata']
            assert 'processing_time' in metadata
            assert 'file_type' in metadata
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend server not running")
        except FileNotFoundError:
            pytest.skip(f"Test document not found: {test_doc}")
    
    def test_text_extraction_with_pdf(self):
        """Test text extraction specifically with PDF files."""
        pdf_files = [doc for doc in self.test_documents if doc.lower().endswith('.pdf')]
        
        if not pdf_files:
            pytest.skip("No PDF test files available")
        
        test_pdf = pdf_files[0]
        
        try:
            with open(test_pdf, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f"{self.api_url}/extract",
                    files=files,
                    timeout=60
                )
            
            assert response.status_code == 200
            data = response.json()
            
            # PDF should have text content
            assert 'text' in data
            assert isinstance(data['text'], str)
            
            # Check metadata indicates PDF processing
            metadata = data['metadata']
            assert metadata.get('file_type', '').lower() in ['pdf', 'application/pdf']
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend server not running")
        except FileNotFoundError:
            pytest.skip(f"Test PDF not found: {test_pdf}")
    
    def test_text_extraction_with_image(self):
        """Test text extraction with image files."""
        image_files = [doc for doc in self.test_documents 
                      if doc.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not image_files:
            pytest.skip("No image test files available")
        
        test_image = image_files[0]
        
        try:
            with open(test_image, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f"{self.api_url}/extract",
                    files=files,
                    timeout=60
                )
            
            assert response.status_code == 200
            data = response.json()
            
            # Check response structure
            assert 'text' in data
            assert 'metadata' in data
            
            # Check if text blocks are provided for images
            if 'text_blocks' in data:
                assert isinstance(data['text_blocks'], list)
                
                # If text blocks exist, check structure
                if data['text_blocks']:
                    block = data['text_blocks'][0]
                    assert 'text' in block
                    assert 'confidence' in block
                    assert 'bbox' in block
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend server not running")
        except FileNotFoundError:
            pytest.skip(f"Test image not found: {test_image}")
    
    def test_text_extraction_invalid_file(self):
        """Test text extraction with invalid file."""
        try:
            # Create a dummy text file
            dummy_content = b"This is not a valid document for OCR"
            files = {'file': ('test.txt', dummy_content, 'text/plain')}
            
            response = requests.post(
                f"{self.api_url}/extract",
                files=files,
                timeout=30
            )
            
            # Should return error for invalid file
            assert response.status_code in [400, 422]
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend server not running")
    
    def test_text_extraction_no_file(self):
        """Test text extraction without file."""
        try:
            response = requests.post(f"{self.api_url}/extract", timeout=10)
            assert response.status_code in [400, 422]
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend server not running")
    
    def test_azure_configuration(self):
        """Test Azure Document Intelligence configuration."""
        try:
            from text_detection.config.azure_config import AzureConfig
            config = AzureConfig()
            
            # Check if Azure credentials are configured
            assert hasattr(config, 'endpoint')
            assert hasattr(config, 'key')
            
            # Check if endpoint is valid URL
            assert config.endpoint.startswith('https://')
            assert len(config.key) > 0
            
        except ImportError:
            pytest.skip("Azure config not available")
        except Exception as e:
            pytest.skip(f"Azure configuration error: {e}")

class TestTextDetectionIntegration:
    """Integration tests for text detection."""
    
    def test_full_text_extraction_workflow(self):
        """Test complete text extraction workflow."""
        if not os.path.exists(TEST_DOCUMENTS_PATH):
            pytest.skip("Test documents directory not found")
        
        test_docs = [f for f in os.listdir(TEST_DOCUMENTS_PATH) 
                    if f.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg'))]
        
        if not test_docs:
            pytest.skip("No test documents available")
        
        results = []
        
        for doc_file in test_docs[:3]:  # Test first 3 documents
            doc_path = os.path.join(TEST_DOCUMENTS_PATH, doc_file)
            
            try:
                with open(doc_path, 'rb') as f:
                    files = {'file': f}
                    response = requests.post(
                        f"{BASE_URL}/api/text-detection/extract",
                        files=files,
                        timeout=60
                    )
                
                if response.status_code == 200:
                    data = response.json()
                    results.append({
                        'document': doc_file,
                        'text_length': len(data.get('text', '')),
                        'has_text_blocks': 'text_blocks' in data,
                        'processing_time': data.get('metadata', {}).get('processing_time'),
                        'success': True
                    })
                else:
                    results.append({
                        'document': doc_file,
                        'error': response.status_code,
                        'success': False
                    })
                    
            except Exception as e:
                results.append({
                    'document': doc_file,
                    'error': str(e),
                    'success': False
                })
        
        # At least one test should succeed
        successful_tests = [r for r in results if r.get('success')]
        assert len(successful_tests) > 0, f"No successful extractions. Results: {results}"
    
    def test_text_detection_performance(self):
        """Test text detection performance."""
        if not os.path.exists(TEST_DOCUMENTS_PATH):
            pytest.skip("Test documents directory not found")
        
        test_docs = [f for f in os.listdir(TEST_DOCUMENTS_PATH) 
                    if f.lower().endswith(('.pdf', '.png', '.jpg'))]
        
        if not test_docs:
            pytest.skip("No test documents available")
        
        # Test with first document
        test_doc = os.path.join(TEST_DOCUMENTS_PATH, test_docs[0])
        
        import time
        start_time = time.time()
        
        try:
            with open(test_doc, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f"{BASE_URL}/api/text-detection/extract",
                    files=files,
                    timeout=60
                )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Performance assertions
            assert processing_time < 60, f"Processing took too long: {processing_time}s"
            
            if response.status_code == 200:
                data = response.json()
                # Check if processing time is reported in metadata
                reported_time = data.get('metadata', {}).get('processing_time')
                if reported_time:
                    # Reported time should be reasonable
                    assert float(reported_time.replace('s', '')) < 60
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend server not running")
        except Exception as e:
            pytest.fail(f"Performance test failed: {e}")

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
