"""
Test suite for component detection functionality.
Tests the YOLO-based electrical component detection system.
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
TEST_IMAGE_PATH = "component_detection/sample_images"

class TestComponentDetection:
    """Test cases for component detection API."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        self.api_url = f"{BASE_URL}/api/component-detection"
        self.test_images = self._get_test_images()
    
    def _get_test_images(self):
        """Get list of test images."""
        test_images = []
        if os.path.exists(TEST_IMAGE_PATH):
            for file in os.listdir(TEST_IMAGE_PATH):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    test_images.append(os.path.join(TEST_IMAGE_PATH, file))
        return test_images
    
    def test_health_endpoint(self):
        """Test if the health endpoint is working."""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=10)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend server not running")
    
    def test_component_detection_endpoint_exists(self):
        """Test if component detection endpoint exists."""
        try:
            response = requests.options(f"{self.api_url}/detect")
            assert response.status_code in [200, 405]  # 405 is OK for OPTIONS
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend server not running")
    
    def test_component_detection_with_valid_image(self):
        """Test component detection with a valid image."""
        if not self.test_images:
            pytest.skip("No test images available")
        
        test_image = self.test_images[0]
        
        try:
            with open(test_image, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f"{self.api_url}/detect",
                    files=files,
                    timeout=30
                )
            
            assert response.status_code == 200
            data = response.json()
            
            # Check response structure
            assert 'detections' in data
            assert 'metadata' in data
            assert isinstance(data['detections'], list)
            
            # If detections found, check structure
            if data['detections']:
                detection = data['detections'][0]
                required_fields = ['class_name', 'confidence', 'bbox']
                for field in required_fields:
                    assert field in detection
                    
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend server not running")
        except FileNotFoundError:
            pytest.skip(f"Test image not found: {test_image}")
    
    def test_component_detection_invalid_file(self):
        """Test component detection with invalid file."""
        try:
            # Create a dummy text file
            dummy_content = b"This is not an image"
            files = {'file': ('test.txt', dummy_content, 'text/plain')}
            
            response = requests.post(
                f"{self.api_url}/detect",
                files=files,
                timeout=10
            )
            
            # Should return error for invalid file
            assert response.status_code in [400, 422]
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend server not running")
    
    def test_component_detection_no_file(self):
        """Test component detection without file."""
        try:
            response = requests.post(f"{self.api_url}/detect", timeout=10)
            assert response.status_code in [400, 422]
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend server not running")
    
    def test_electrical_component_classes(self):
        """Test that all expected electrical component classes are supported."""
        expected_classes = [
            "Ammeter", "Cable Termination Box", "Earth Electrode",
            "Single Phase Tap-Off Unit", "voltmeter"
        ]
        
        # This test would need access to the component mapper
        # For now, just check if we can import it
        try:
            from component_detection.electrical_mapper import ElectricalComponentMapper
            mapper = ElectricalComponentMapper()
            
            # Check if expected classes are in the mapper
            available_classes = list(mapper.electrical_classes.values())
            
            for expected_class in expected_classes:
                assert expected_class in available_classes, f"Missing class: {expected_class}"
                
        except ImportError:
            pytest.skip("Component mapper not available")

class TestComponentDetectionIntegration:
    """Integration tests for component detection."""
    
    def test_full_detection_workflow(self):
        """Test complete detection workflow."""
        if not os.path.exists(TEST_IMAGE_PATH):
            pytest.skip("Test images directory not found")
        
        test_images = [f for f in os.listdir(TEST_IMAGE_PATH) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not test_images:
            pytest.skip("No test images available")
        
        results = []
        
        for image_file in test_images[:3]:  # Test first 3 images
            image_path = os.path.join(TEST_IMAGE_PATH, image_file)
            
            try:
                with open(image_path, 'rb') as f:
                    files = {'file': f}
                    response = requests.post(
                        f"{BASE_URL}/api/component-detection/detect",
                        files=files,
                        timeout=30
                    )
                
                if response.status_code == 200:
                    data = response.json()
                    results.append({
                        'image': image_file,
                        'detections': len(data.get('detections', [])),
                        'success': True
                    })
                else:
                    results.append({
                        'image': image_file,
                        'error': response.status_code,
                        'success': False
                    })
                    
            except Exception as e:
                results.append({
                    'image': image_file,
                    'error': str(e),
                    'success': False
                })
        
        # At least one test should succeed
        successful_tests = [r for r in results if r.get('success')]
        assert len(successful_tests) > 0, f"No successful detections. Results: {results}"

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
