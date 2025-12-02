"""
Performance Testing Framework for SLD Processing Platform.
Measures and analyzes performance of component detection and text extraction.
"""

import time
import statistics
import json
import os
import requests
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    operation: str
    duration: float
    success: bool
    timestamp: datetime
    file_size: int = 0
    detections_count: int = 0
    error_message: str = ""

class PerformanceTester:
    """Main performance testing class."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[PerformanceMetric] = []
        self.test_images_dir = "component_detection/sample_images"
        self.test_documents_dir = "text_detection/uploads"
    
    def test_component_detection_performance(self, iterations: int = 10) -> Dict[str, Any]:
        """Test component detection performance."""
        print(f"🔍 Testing component detection performance ({iterations} iterations)")
        
        test_images = self._get_test_files(self.test_images_dir, ['.png', '.jpg', '.jpeg'])
        if not test_images:
            print("❌ No test images found")
            return {"error": "No test images available"}
        
        metrics = []
        
        for i in range(iterations):
            for image_path in test_images[:3]:  # Test first 3 images
                metric = self._test_single_component_detection(image_path)
                metrics.append(metric)
                self.results.append(metric)
                
                print(f"  Iteration {i+1}/{iterations}, Image: {Path(image_path).name}, "
                      f"Duration: {metric.duration:.2f}s, Success: {metric.success}")
        
        return self._analyze_metrics(metrics, "Component Detection")
    
    def test_text_detection_performance(self, iterations: int = 5) -> Dict[str, Any]:
        """Test text detection performance."""
        print(f"📄 Testing text detection performance ({iterations} iterations)")
        
        test_files = self._get_test_files(self.test_documents_dir, ['.pdf', '.png', '.jpg'])
        if not test_files:
            print("❌ No test documents found")
            return {"error": "No test documents available"}
        
        metrics = []
        
        for i in range(iterations):
            for file_path in test_files[:2]:  # Test first 2 files
                metric = self._test_single_text_detection(file_path)
                metrics.append(metric)
                self.results.append(metric)
                
                print(f"  Iteration {i+1}/{iterations}, File: {Path(file_path).name}, "
                      f"Duration: {metric.duration:.2f}s, Success: {metric.success}")
        
        return self._analyze_metrics(metrics, "Text Detection")
    
    def test_concurrent_performance(self, concurrent_requests: int = 5) -> Dict[str, Any]:
        """Test performance under concurrent load."""
        print(f"⚡ Testing concurrent performance ({concurrent_requests} concurrent requests)")
        
        test_images = self._get_test_files(self.test_images_dir, ['.png', '.jpg', '.jpeg'])
        if not test_images:
            return {"error": "No test images available"}
        
        # Use the first test image for all concurrent requests
        test_image = test_images[0]
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [
                executor.submit(self._test_single_component_detection, test_image)
                for _ in range(concurrent_requests)
            ]
            
            metrics = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    metric = future.result()
                    metrics.append(metric)
                    self.results.append(metric)
                except Exception as e:
                    print(f"❌ Concurrent test error: {e}")
        
        total_time = time.time() - start_time
        
        analysis = self._analyze_metrics(metrics, "Concurrent Requests")
        analysis["total_concurrent_time"] = total_time
        analysis["requests_per_second"] = len(metrics) / total_time if total_time > 0 else 0
        
        return analysis
    
    def test_memory_usage(self) -> Dict[str, Any]:
        """Test memory usage during operations."""
        print("💾 Testing memory usage")
        
        try:
            import psutil
            process = psutil.Process()
            
            # Baseline memory
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Run some operations
            self.test_component_detection_performance(iterations=3)
            
            # Peak memory
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            return {
                "baseline_memory_mb": baseline_memory,
                "peak_memory_mb": peak_memory,
                "memory_increase_mb": peak_memory - baseline_memory,
                "memory_increase_percent": ((peak_memory - baseline_memory) / baseline_memory) * 100
            }
            
        except ImportError:
            return {"error": "psutil not available for memory testing"}
    
    def _test_single_component_detection(self, image_path: str) -> PerformanceMetric:
        """Test single component detection operation."""
        start_time = time.time()
        
        try:
            file_size = os.path.getsize(image_path)
            
            with open(image_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f"{self.base_url}/api/component-detection/detect",
                    files=files,
                    timeout=30
                )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                detections_count = len(data.get('detections', []))
                
                return PerformanceMetric(
                    operation="component_detection",
                    duration=duration,
                    success=True,
                    timestamp=datetime.now(),
                    file_size=file_size,
                    detections_count=detections_count
                )
            else:
                return PerformanceMetric(
                    operation="component_detection",
                    duration=duration,
                    success=False,
                    timestamp=datetime.now(),
                    file_size=file_size,
                    error_message=f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            duration = time.time() - start_time
            return PerformanceMetric(
                operation="component_detection",
                duration=duration,
                success=False,
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    def _test_single_text_detection(self, file_path: str) -> PerformanceMetric:
        """Test single text detection operation."""
        start_time = time.time()
        
        try:
            file_size = os.path.getsize(file_path)
            
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f"{self.base_url}/api/text-detection/extract",
                    files=files,
                    timeout=60
                )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                text_length = len(data.get('text', ''))
                
                return PerformanceMetric(
                    operation="text_detection",
                    duration=duration,
                    success=True,
                    timestamp=datetime.now(),
                    file_size=file_size,
                    detections_count=text_length  # Use text length as metric
                )
            else:
                return PerformanceMetric(
                    operation="text_detection",
                    duration=duration,
                    success=False,
                    timestamp=datetime.now(),
                    file_size=file_size,
                    error_message=f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            duration = time.time() - start_time
            return PerformanceMetric(
                operation="text_detection",
                duration=duration,
                success=False,
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    def _get_test_files(self, directory: str, extensions: List[str]) -> List[str]:
        """Get test files from directory."""
        if not os.path.exists(directory):
            return []
        
        files = []
        for file in os.listdir(directory):
            if any(file.lower().endswith(ext) for ext in extensions):
                files.append(os.path.join(directory, file))
        
        return files
    
    def _analyze_metrics(self, metrics: List[PerformanceMetric], operation_name: str) -> Dict[str, Any]:
        """Analyze performance metrics."""
        if not metrics:
            return {"error": "No metrics to analyze"}
        
        successful_metrics = [m for m in metrics if m.success]
        failed_metrics = [m for m in metrics if not m.success]
        
        if not successful_metrics:
            return {
                "operation": operation_name,
                "total_tests": len(metrics),
                "successful_tests": 0,
                "failed_tests": len(failed_metrics),
                "success_rate": 0.0,
                "errors": [m.error_message for m in failed_metrics]
            }
        
        durations = [m.duration for m in successful_metrics]
        
        return {
            "operation": operation_name,
            "total_tests": len(metrics),
            "successful_tests": len(successful_metrics),
            "failed_tests": len(failed_metrics),
            "success_rate": len(successful_metrics) / len(metrics),
            "performance": {
                "avg_duration": statistics.mean(durations),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "median_duration": statistics.median(durations),
                "std_deviation": statistics.stdev(durations) if len(durations) > 1 else 0
            },
            "throughput": {
                "operations_per_second": len(successful_metrics) / sum(durations) if sum(durations) > 0 else 0
            }
        }
    
    def generate_report(self, output_file: str = "performance_report.json"):
        """Generate comprehensive performance report."""
        print(f"📊 Generating performance report: {output_file}")
        
        # Run all tests
        component_results = self.test_component_detection_performance()
        text_results = self.test_text_detection_performance()
        concurrent_results = self.test_concurrent_performance()
        memory_results = self.test_memory_usage()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "test_summary": {
                "total_operations": len(self.results),
                "successful_operations": len([r for r in self.results if r.success]),
                "failed_operations": len([r for r in self.results if not r.success])
            },
            "component_detection": component_results,
            "text_detection": text_results,
            "concurrent_performance": concurrent_results,
            "memory_usage": memory_results,
            "raw_metrics": [
                {
                    "operation": m.operation,
                    "duration": m.duration,
                    "success": m.success,
                    "timestamp": m.timestamp.isoformat(),
                    "file_size": m.file_size,
                    "detections_count": m.detections_count,
                    "error_message": m.error_message
                }
                for m in self.results
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Performance report saved to {output_file}")
        return report

def main():
    """Main function to run performance tests."""
    print("🚀 Starting SLD Platform Performance Testing")
    
    tester = PerformanceTester()
    
    # Check if server is running
    try:
        response = requests.get(f"{tester.base_url}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server health check failed")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Please start the backend first.")
        return
    
    # Generate comprehensive report
    report = tester.generate_report()
    
    # Print summary
    print("\n📊 Performance Test Summary:")
    print(f"Total operations: {report['test_summary']['total_operations']}")
    print(f"Successful: {report['test_summary']['successful_operations']}")
    print(f"Failed: {report['test_summary']['failed_operations']}")
    
    if 'performance' in report.get('component_detection', {}):
        perf = report['component_detection']['performance']
        print(f"Component Detection - Avg: {perf['avg_duration']:.2f}s, "
              f"Min: {perf['min_duration']:.2f}s, Max: {perf['max_duration']:.2f}s")

if __name__ == "__main__":
    main()
